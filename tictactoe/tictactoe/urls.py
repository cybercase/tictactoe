from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
from rest_framework import routers
from core.views import GameListViewSet, \
    GameDetailViewSet, \
    UserViewSet, \
    MeViewSet, \
    StatsViewSet

admin.autodiscover()

router = routers.DefaultRouter()

router.register(r'me', MeViewSet, 'me')
router.register(r'users', UserViewSet)
router.register(r'stats', StatsViewSet)
router.register(r'games', GameListViewSet)
router.register(r'games', GameDetailViewSet)

urlpatterns = router.urls

urlpatterns += patterns('',
    # Examples:
    # url(r'^$', 'trisgame.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    url(r'^index/', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^accounts/', include('registration.backends.simple.urls')),

    url(r'^api-token-auth', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
)
