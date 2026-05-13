"""Daily notification scheduler task for Constellab Care.

Register this Task in the Constellab platform as a CRON-triggered job
(e.g. ``0 6 * * *`` for every day at 06:00) to automatically send:

- J-15 appointment reminders
- J-3 appointment reminders
- J-1 appointment reminders
"""

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    InputSpecs,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)

from gws_care.notification.notification_service import NotificationService


@task_decorator(
    "CareNotificationScheduler",
    human_name="Care — Notification Scheduler",
    short_description="Sends daily appointment reminders (J-15, J-3, J-1).",
)
class CareNotificationSchedulerTask(Task):
    """Daily scheduler task that dispatches appointment reminders.

    Designed to be executed once per day via a CRON-triggered job
    (e.g. ``0 6 * * *``).

    The task is fully **idempotent**: re-running it on the same day will not
    send duplicate reminders, because each reminder type is tracked via a
    distinct ``NotificationType`` in the ``NotificationLog``.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        count = NotificationService.send_daily_appointment_reminders()
        self.log_info_message(f"Notification scheduler completed: {count} reminder(s) sent.")
        return {}
