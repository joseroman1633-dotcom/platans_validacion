from django import forms

MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError("Debes seleccionar al menos una imagen.")
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned_files = []
        errors = []
        single_file_clean = super().clean

        for file in data:
            try:
                cleaned_file = single_file_clean(file, initial)

                if cleaned_file.size > MAX_IMAGE_SIZE_BYTES:
                    raise forms.ValidationError(
                        f"Cada imagen debe pesar como máximo {MAX_IMAGE_SIZE_MB} MB."
                    )

                cleaned_file.seek(0)
                cleaned_files.append(cleaned_file)
            except forms.ValidationError as exc:
                errors.extend(exc.error_list)

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_files


class MultipleImageUploadForm(forms.Form):
    imagenes = MultipleImageField(
        label="Seleccionar imágenes",
        required=True,
    )

    tipo_origen = forms.ChoiceField(
        choices=[
            ("IA", "Imagen generada por IA"),
            ("NO_IA", "Imagen no generada por IA"),
        ],
        label="Tipo de imagen",
    )

    seleccionada = forms.BooleanField(
        required=False,
        initial=True,
        label="Guardar también en base64",
    )

    activa = forms.BooleanField(
        required=False,
        initial=True,
        label="Activa",
    )
