"""URL configuration for the project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.views import localized_static_page, set_language
from products.views import ProductListView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("language/<str:code>/", set_language, name="set_language"),
    path("", ProductListView.as_view(), name="home"),
    path("", include("products.urls")),
    path("", include("users.urls")),
    path("", include("orders.urls")),
    path("community/", localized_static_page("community"), name="community"),
    path("resources/", localized_static_page("resources"), name="resources"),
    path("contact/", localized_static_page("contact"), name="contact"),
    path("faq/", localized_static_page("faq"), name="faq"),
    path("license/", localized_static_page("license"), name="license"),
    path("guides/", localized_static_page("guides"), name="guides"),
    path("api/", include("api.urls")),
    path("graphql/", include("api.graphql_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
