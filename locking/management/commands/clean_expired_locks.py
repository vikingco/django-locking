from django.core.management.base import BaseCommand

from locking.models import NonBlockingLock

from logging import getLogger
logger = getLogger(__name__)


class Command(BaseCommand):
    help_text = 'Remove expired locks'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run',
                            action='store_true',
                            dest='dry_run',
                            default=False,
                            help='Just say how many we would remove, but don\'t actually do it')

    def handle(self, **options):
        locks = NonBlockingLock.objects.get_expired_locks()
        if options['dry_run']:
            logger.info('Would delete %s locks' % len(locks))
        else:
            locks.delete()
