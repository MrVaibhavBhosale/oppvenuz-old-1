from .models import SavedTemplate

def add_favorite(user, template):
    favorite = SavedTemplate.objects.create(user=user, template=template)
    return favorite

def remove_favorite(user, template):
    favorite = SavedTemplate.objects.get(user=user, template=template)
    favorite.delete()

def get_user_favorites(user):
    favorites = SavedTemplate.objects.filter(user=user)
    return favorites

def is_template_favorited(user, template):
    """Checks if a user has favorited a template using ManyToManyField."""
    return template in user.saved_templates.all()

def toggle_favorite(user, template):
    """Toggles a template as favorite for the user."""
    try:
        favorite = SavedTemplate.objects.get(user=user, template=template)
        favorite.delete()
        return 0
    except SavedTemplate.DoesNotExist:
        favorite = SavedTemplate.objects.create(user=user, template=template)
        return 1