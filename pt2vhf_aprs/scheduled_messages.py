from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from . import database as db
from . import diagnostics as diag
from .aprs_service import service as aprs_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt.astimezone(timezone.utc)


def _next_weekly(weekday: int, time_local: str, after: datetime | None = None) -> datetime:
    now_utc = after or _utc_now()
    local_tz = datetime.now().astimezone().tzinfo
    now_local = now_utc.astimezone(local_tz)
    hour, minute = [int(part) for part in str(time_local).split(":", 1)]
    days = (int(weekday) - now_local.weekday()) % 7
    candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days)
    if candidate <= now_local:
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc)


def prepare_schedule_payload(data: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(data or {})
    schedule_type = str(payload.get("schedule_type") or "once").lower().strip()
    enabled = bool(payload.get("enabled", True))

    if schedule_type == "once":
        run_at = _parse_iso(payload.get("run_at_utc"))
        if not run_at:
            raise ValueError("Informe a data e hora do envio único.")
        if run_at <= _utc_now() - timedelta(minutes=1):
            raise ValueError("A data/hora do envio deve estar no futuro.")
        payload["run_at_utc"] = run_at.isoformat(timespec="seconds")
        payload["weekday"] = None
        payload["time_local"] = None
        payload["next_run_at"] = run_at.isoformat(timespec="seconds") if enabled else None
    elif schedule_type == "weekly":
        weekday = int(payload.get("weekday"))
        time_local = str(payload.get("time_local") or "").strip()
        if weekday < 0 or weekday > 6:
            raise ValueError("Dia da semana inválido.")
        if len(time_local) != 5 or time_local[2] != ":":
            raise ValueError("Horário semanal inválido.")
        hour, minute = [int(part) for part in time_local.split(":", 1)]
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Horário semanal inválido.")
        payload["weekday"] = weekday
        payload["time_local"] = f"{hour:02d}:{minute:02d}"
        payload["run_at_utc"] = None
        payload["next_run_at"] = _next_weekly(weekday, payload["time_local"]).isoformat(timespec="seconds") if enabled else None
    else:
        raise ValueError("Tipo de agendamento inválido.")

    return payload


def calculate_next_run(schedule: dict[str, Any], *, after: datetime | None = None) -> str | None:
    if not schedule.get("enabled"):
        return None
    if str(schedule.get("schedule_type") or "") == "weekly":
        return _next_weekly(
            int(schedule.get("weekday")),
            str(schedule.get("time_local") or "00:00"),
            after=after,
        ).isoformat(timespec="seconds")
    return None


def _recipient_calls(schedule: dict[str, Any]) -> list[str]:
    target_type = str(schedule.get("target_type") or "station")
    if target_type == "station":
        call = str(schedule.get("target") or "").upper().strip()
        return [call] if call else []
    if target_type != "list":
        return []

    calls = [str(item).upper().strip() for item in schedule.get("targets") or [] if str(item).strip()]
    group_id = schedule.get("recipient_group_id")
    if group_id:
        for group in db.list_recipient_groups():
            if int(group.get("id") or 0) == int(group_id):
                calls.extend(group.get("callsigns") or [])
                break
    result: list[str] = []
    for call in calls:
        if call and call not in result:
            result.append(call)
    return result


class ScheduledMessageService:
    def __init__(self) -> None:
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._manual_lock = threading.Lock()

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._recover_interrupted()
        self._worker = threading.Thread(
            target=self._loop,
            name="aprs-scheduled-messages",
            daemon=True,
        )
        self._worker.start()
        diag.log_event("scheduled_messages_started")

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def wake(self) -> None:
        self._wake.set()

    def _recover_interrupted(self) -> None:
        for schedule in db.list_scheduled_messages():
            if schedule.get("last_status") != "running" or schedule.get("next_run_at"):
                continue
            if str(schedule.get("schedule_type")) == "weekly" and schedule.get("enabled"):
                next_run = calculate_next_run(schedule)
                db.complete_scheduled_message(
                    int(schedule["id"]),
                    status="interrompido",
                    error="A execução anterior foi interrompida pelo encerramento do Client.",
                    next_run_at=next_run,
                    enabled=True,
                )
            else:
                db.complete_scheduled_message(
                    int(schedule["id"]),
                    status="interrompido",
                    error="A execução anterior foi interrompida pelo encerramento do Client.",
                    next_run_at=None,
                    enabled=False,
                )

    def _loop(self) -> None:
        while not self._stop.is_set():
            schedule = db.claim_due_scheduled_message(_utc_now().isoformat(timespec="seconds"))
            if not schedule:
                self._wake.wait(10.0)
                self._wake.clear()
                continue
            self._execute_claimed(schedule)

    def execute_now(self, schedule_id: int) -> None:
        schedule = db.get_scheduled_message(schedule_id)
        if not schedule:
            raise ValueError("Agendamento não encontrado.")

        def _run() -> None:
            with self._manual_lock:
                ok, summary, error = self._execute(schedule, manual=True)
                db.complete_scheduled_message(
                    int(schedule["id"]),
                    status="concluído manual" if ok else "falhou manual",
                    error=error,
                    summary=summary,
                    next_run_at=schedule.get("next_run_at"),
                    enabled=bool(schedule.get("enabled")),
                )

        threading.Thread(
            target=_run,
            name=f"aprs-scheduled-manual-{int(schedule_id)}",
            daemon=True,
        ).start()

    def _send_one(self, schedule: dict[str, Any], destination: str | None = None) -> dict[str, Any]:
        target_type = str(schedule.get("target_type") or "station")
        message = str(schedule.get("message") or "")
        if target_type in {"station", "list"}:
            return aprs_service.queue_message_parts(
                destination or "",
                message,
                route=str(schedule.get("route") or "auto"),
                path=str(schedule.get("path") or ""),
            )

        if target_type == "group":
            row_id = aprs_service.send_bulletin(
                message,
                bulletin_id=str(schedule.get("bulletin_id") or "0"),
                group=str(schedule.get("aprs_group") or schedule.get("target") or ""),
            )
            return {"id": row_id, "type": "group_bulletin"}

        bulletin_id = str(schedule.get("bulletin_id") or "0")
        if str(schedule.get("message_type") or "") == "announcement" and not bulletin_id.isalpha():
            bulletin_id = "A"
        row_id = aprs_service.send_bulletin(message, bulletin_id=bulletin_id, group="")
        return {"id": row_id, "type": str(schedule.get("message_type") or "bulletin")}

    def _execute(self, schedule: dict[str, Any], *, manual: bool = False) -> tuple[bool, str, str]:
        schedule_id = int(schedule["id"])
        targets = _recipient_calls(schedule)
        target_type = str(schedule.get("target_type") or "station")
        if target_type in {"station", "list"} and not targets:
            error = "Nenhum destinatário válido configurado."
            if manual:
                diag.log_event("scheduled_message_manual_failed", schedule_id=schedule_id, error=error)
            return False, "", error

        successes: list[str] = []
        failures: list[str] = []
        items: list[str | None] = targets if target_type in {"station", "list"} else [None]
        interval = max(1, min(120, int(schedule.get("interval_seconds") or 3)))
        continue_on_error = bool(schedule.get("continue_on_error", True))

        for index, destination in enumerate(items):
            try:
                self._send_one(schedule, destination)
                successes.append(destination or target_type)
            except Exception as exc:
                label = destination or target_type
                failures.append(f"{label}: {exc}")
                if not continue_on_error:
                    break
            if index + 1 < len(items) and not self._stop.is_set():
                self._stop.wait(interval)

        success_detail = ", ".join(successes)
        failure_detail = " | ".join(failures)
        summary = f"{len(successes)} sucesso(s), {len(failures)} falha(s)"
        if success_detail:
            summary += f" · OK: {success_detail}"
        if failure_detail:
            summary += f" · Falhas: {failure_detail}"
        error = failure_detail
        ok = not failures
        diag.log_event(
            "scheduled_message_executed",
            schedule_id=schedule_id,
            manual=manual,
            successes=len(successes),
            failures=len(failures),
            target_type=target_type,
        )
        return ok, summary, error

    def _execute_claimed(self, schedule: dict[str, Any]) -> None:
        schedule_id = int(schedule["id"])
        ok, summary, error = self._execute(schedule, manual=False)
        now = _utc_now()

        if ok:
            if str(schedule.get("schedule_type")) == "weekly":
                next_run = calculate_next_run(schedule, after=now + timedelta(seconds=1))
                db.complete_scheduled_message(
                    schedule_id,
                    status="concluído",
                    summary=summary,
                    next_run_at=next_run,
                    enabled=True,
                )
            else:
                db.complete_scheduled_message(
                    schedule_id,
                    status="concluído",
                    summary=summary,
                    next_run_at=None,
                    enabled=False,
                )
            return

        if str(schedule.get("retry_policy") or "skip") == "retry":
            retry_at = now + timedelta(minutes=max(1, int(schedule.get("retry_minutes") or 10)))
            db.complete_scheduled_message(
                schedule_id,
                status="aguardando retry",
                error=error,
                summary=summary,
                next_run_at=retry_at.isoformat(timespec="seconds"),
                enabled=True,
            )
        elif str(schedule.get("schedule_type")) == "weekly":
            next_run = calculate_next_run(schedule, after=now + timedelta(seconds=1))
            db.complete_scheduled_message(
                schedule_id,
                status="falhou",
                error=error,
                summary=summary,
                next_run_at=next_run,
                enabled=True,
            )
        else:
            db.complete_scheduled_message(
                schedule_id,
                status="falhou",
                error=error,
                summary=summary,
                next_run_at=None,
                enabled=False,
            )


service = ScheduledMessageService()
