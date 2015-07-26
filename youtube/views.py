from __future__ import unicode_literals
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import format_html
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Video, Channel
from .forms import AddChannelForm


def index(request):
    return render(request, 'youtube/index.html', {
        'videos': (Video.objects.
                   filter(uploader__hidden=False).
                   exclude_deleted().
                   prefetch_related('uploader')),
    })


def channel(request, author):
    # Basic queryset for channel, prefetching video entries.
    qs = Channel.objects.prefetch_related('videos')

    # If we're not logged in, don't allow showing hidden channels.
    if not request.user.is_authenticated():
        qs = qs.filter(hidden=False)

    # Fetch the channel, or 404.
    channel = get_object_or_404(qs, author=author)

    # Render and return.
    return render(request, 'youtube/index.html', {
        'videos': channel.videos.exclude_deleted(),
    })


@login_required
def admin(request):
    form = AddChannelForm(request.POST or None)
    return render(request, 'youtube/admin.html', {
        'admin_channels': (Channel.objects.
                           prefetch_related('videos').
                           order_by('hidden', 'title')),
        'form': form,
        'page': 'admin',
    })


@require_POST
@login_required
@transaction.atomic
def channel_delete(request, channelid):
    channel = get_object_or_404(Channel, pk=channelid)
    title = channel.title
    channel.delete()
    messages.success(request, format_html(
        'Channel with the title removed: <b>{0}</b>',
        title))
    return redirect('admin')


@require_POST
@login_required
@transaction.atomic
def channel_add(request):
    form = AddChannelForm(request.POST)

    if not form.is_valid():
        return admin(request)

    channel = Channel.objects.create(author=form.cleaned_data['channel'])
    channel.update_channel_info()
    channel.fetch_videos()

    messages.success(request, format_html(
        'Added channel under name <b>{0}</b>',
        channel.title))

    return redirect('admin')


@require_POST
@login_required
@transaction.atomic
def toggle_hidden(request, channelid):
    channel = get_object_or_404(Channel, pk=channelid)
    channel.hidden = not channel.hidden
    channel.save(update_fields=['hidden'])
    messages.success(request, format_html(
        'Visibility of channel <b>{0}</b> changed.',
        channel.title))
    return redirect('admin')
