from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from validacion.models import ImagenValidacion


class Command(BaseCommand):
    help = (
        "Sube a Cloudinary las imagenes existentes guardadas localmente en media/ "
        "y actualiza el campo imagen cuando Cloudinary devuelve un public_id distinto."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--media-root",
            default=None,
            help="Ruta local donde existen actualmente las imagenes. Por defecto usa ./media",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Vuelve a subir las imagenes aunque ya existan en Cloudinary.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_CLOUDINARY", False):
            raise CommandError(
                "Activa USE_CLOUDINARY=True y configura CLOUDINARY_URL antes de ejecutar este comando."
            )

        media_root = Path(options["media_root"] or (settings.BASE_DIR / "media")).resolve()
        if not media_root.exists():
            raise CommandError(f"No existe la carpeta media local: {media_root}")

        total = 0
        synced = 0
        skipped = 0
        missing = 0

        queryset = ImagenValidacion.objects.exclude(imagen="").order_by("id")

        for imagen_validacion in queryset:
            total += 1
            nombre_actual = imagen_validacion.imagen.name
            local_file = media_root / nombre_actual

            if not local_file.exists():
                missing += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"No se encontro el archivo local para ID {imagen_validacion.id}: {local_file}"
                    )
                )
                continue

            if not options["force"]:
                try:
                    if default_storage.exists(nombre_actual):
                        skipped += 1
                        self.stdout.write(
                            f"Ya existe en Cloudinary, se omite ID {imagen_validacion.id}: {nombre_actual}"
                        )
                        continue
                except Exception:
                    # Si la comprobacion remota falla, intentamos subir el archivo.
                    pass

            with local_file.open("rb") as fh:
                nuevo_nombre = default_storage.save(nombre_actual, File(fh, name=local_file.name))

            if nuevo_nombre != nombre_actual:
                imagen_validacion.imagen.name = nuevo_nombre
                imagen_validacion.save(update_fields=["imagen"])

            synced += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sincronizada ID {imagen_validacion.id}: {nombre_actual} -> {imagen_validacion.imagen.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso finalizado. Total={total}, sincronizadas={synced}, omitidas={skipped}, faltantes={missing}"
            )
        )
