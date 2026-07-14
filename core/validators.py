from django.core.exceptions import ValidationError


def validate_image_file(image):
    """Validate uploaded image: format and max size (5 MB)."""
    max_size_mb = 5
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']

    if image.content_type not in allowed_types:
        raise ValidationError(
            'Only JPEG, PNG, and WebP images are allowed.'
        )

    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            f'Image size must not exceed {max_size_mb} MB.'
        )
