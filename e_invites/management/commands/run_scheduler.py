import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from utilities.scheduler import scheduler, update_placid_templates

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    # Add your command specific details here
    help = "starts a scheduler jobs."

    def handle(self, *args, **options):
        # Place your command logic here
        scheduler.add_job(
            update_placid_templates,
            "interval",
            hours=4,
            id="update_placid_templates",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            replace_existing=True,
            misfire_grace_time=None,
            next_run_time=datetime.now(),
        )
        print("update_placid_templates added successfully!!")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
