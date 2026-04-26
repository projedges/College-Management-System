import gzip
from datetime import datetime
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = 'Create an application data backup and a migration snapshot for recovery drills.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            default=str(settings.BASE_DIR / 'backups'),
            help='Directory where backup artifacts should be stored.',
        )
        parser.add_argument(
            '--gzip',
            action='store_true',
            help='Compress the JSON backup payload.',
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir']).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        dump_buffer = StringIO()
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '--indent',
            '2',
            stdout=dump_buffer,
        )
        payload = dump_buffer.getvalue()

        if options['gzip']:
            data_path = output_dir / f'studentms-backup-{timestamp}.json.gz'
            with gzip.open(data_path, 'wt', encoding='utf-8') as backup_file:
                backup_file.write(payload)
        else:
            data_path = output_dir / f'studentms-backup-{timestamp}.json'
            data_path.write_text(payload, encoding='utf-8')

        migration_buffer = StringIO()
        call_command('showmigrations', '--list', stdout=migration_buffer)
        migration_path = output_dir / f'studentms-migrations-{timestamp}.txt'
        migration_path.write_text(migration_buffer.getvalue(), encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'Data backup written to {data_path}'))
        self.stdout.write(self.style.SUCCESS(f'Migration snapshot written to {migration_path}'))
