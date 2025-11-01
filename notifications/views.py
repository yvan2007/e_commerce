from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Notification


@login_required
def notification_list(request):
    """
    Liste toutes les notifications de l'utilisateur (lues et non lues)
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtres
    filter_status = request.GET.get('filter', 'all')  # all, read, unread
    if filter_status == 'read':
        notifications = notifications.filter(is_read=True)
    elif filter_status == 'unread':
        notifications = notifications.filter(is_read=False)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_count = Notification.objects.filter(user=request.user).count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    read_count = total_count - unread_count
    
    context = {
        'notifications': page_obj,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
        'filter_status': filter_status,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """
    Marquer une notification comme lue
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    if not notification.is_read:
        from django.utils import timezone
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Notification marquée comme lue'})
    
    messages.success(request, _('Notification marquée comme lue.'))
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_as_read(request):
    """
    Marquer toutes les notifications comme lues
    """
    from django.utils import timezone
    
    updated = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{updated} notification(s) marquée(s) comme lue(s)'
        })
    
    messages.success(request, _(f'{updated} notification(s) marquée(s) comme lue(s).'))
    return redirect('notifications:list')


@login_required
@require_POST
def delete_notification(request, notification_id):
    """
    Supprimer une notification individuelle
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Notification supprimée'})
    
    messages.success(request, _('Notification supprimée.'))
    return redirect('notifications:list')


@login_required
@require_POST
def delete_selected_notifications(request):
    """
    Supprimer plusieurs notifications sélectionnées
    """
    notification_ids = request.POST.getlist('notification_ids')
    
    if not notification_ids:
        messages.error(request, _('Aucune notification sélectionnée.'))
        return redirect('notifications:list')
    
    deleted_count = Notification.objects.filter(
        id__in=notification_ids,
        user=request.user
    ).delete()[0]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} notification(s) supprimée(s)'
        })
    
    messages.success(request, _(f'{deleted_count} notification(s) supprimée(s).'))
    return redirect('notifications:list')


@login_required
@require_POST
def delete_all_notifications(request):
    """
    Supprimer toutes les notifications de l'utilisateur
    """
    filter_status = request.POST.get('filter', 'all')
    
    if filter_status == 'read':
        notifications = Notification.objects.filter(user=request.user, is_read=True)
    elif filter_status == 'unread':
        notifications = Notification.objects.filter(user=request.user, is_read=False)
    else:
        notifications = Notification.objects.filter(user=request.user)
    
    deleted_count = notifications.delete()[0]
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} notification(s) supprimée(s)'
        })
    
    messages.success(request, _(f'{deleted_count} notification(s) supprimée(s).'))
    return redirect('notifications:list')

