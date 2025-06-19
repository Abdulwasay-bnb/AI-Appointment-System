from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from .models import UserProfile
from unfold.admin import StackedInline, TabularInline


admin.site.unregister(User)
admin.site.unregister(Group)

# Create an inline admin for UserProfile
class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_is_client_portal_user')
    
    def get_is_client_portal_user(self, obj):
        return obj.userprofile.is_client_portal_user
    get_is_client_portal_user.short_description = 'Client Portal User'
    get_is_client_portal_user.boolean = True

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'is_client_portal_user')
    search_fields = ('user__username', 'user__email')
