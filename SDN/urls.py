# coding=utf-8

from django.conf.urls import url
from django.urls import path

import SDN
from SDN import views

urlpatterns = [
    path('', views.index),
    path('index/', SDN.views.index),
    path('pc/', views.pcInfo),
    path('switch', views.switchInfo),
    path('link', views.linkInfo),
    path('errornode', views.repaire),
    path('repaire',views.xiufu),
    path('testview',views.testview),
    path('rizhi',views.rizhi),
]
