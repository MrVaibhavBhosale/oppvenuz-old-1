"""
This file is used as routes for the e_invites app API's.
"""

from django.conf.urls import url
from e_invites.views import (
    AddInviteTemplateAPIView,
    GetInviteTemplateAPIView,
    InviteTemplateListAPIView,
    SaveOrUnsaveTemplateAPI,
    StartSchedulerAPI,
    TemplateListAPI,
    UpdateInviteTemplateAPIView,
    UserSavedTemplateAPI,
    TemplateDetailAPI,
    InviteTemplateRetrieveAPIView,
    UpdatePlacidTemplateView,
    DistinctTagsAPIView
)

urlpatterns = [
    url('v1/getTemplateTagsList', DistinctTagsAPIView.as_view(), name='getTemplateTagsList'),
    url('v1/userSavedTemplates', UserSavedTemplateAPI.as_view(), name='userSavedTemplates'),
    url("v1/startScheduler", StartSchedulerAPI.as_view(), name="startScheduler"),
    url(
        "v1/saveUnsaveTemplate",
        SaveOrUnsaveTemplateAPI.as_view(),
        name="saveUnsaveTemplate",
    ),
    url('v1/templateDetail/(?P<uuid>.+)', TemplateDetailAPI.as_view(), name="templateDetail"),
    url("v1/templateList", TemplateListAPI.as_view(), name="templateList"),
    url(
        "v1/addInviteTemplate",
        AddInviteTemplateAPIView.as_view(),
        name="addInviteTemplate",
    ),
    url(
        "addInviteTemplate",
        AddInviteTemplateAPIView.as_view(),
        name="addInviteTemplate",
    ),
    url(
        "v1/updateInviteTemplate/(?P<pk>.+)",
        UpdateInviteTemplateAPIView.as_view(),
        name="updateInviteTemplate",
    ),
    url(
        "v1/detailInviteTemplate/(?P<pk>.+)",
        InviteTemplateRetrieveAPIView.as_view(),
        name="detailInviteTemplate",
    ),
    url(
        "updateInviteTemplate/(?P<pk>.+)",
        UpdateInviteTemplateAPIView.as_view(),
        name="updateInviteTemplate",
    ),
    url(
        "v1/inviteTemplateList",
        InviteTemplateListAPIView.as_view(),
        name="inviteTemplateList",
    ),
    url(
        "inviteTemplateList",
        InviteTemplateListAPIView.as_view(),
        name="inviteTemplateList",
    ),
    url(
        "v1/getInviteTemplate/(?P<pk>.+)",
        GetInviteTemplateAPIView.as_view(),
        name="getInviteTemplate",
    ),
    url(
        "getInviteTemplate/(?P<pk>.+)",
        GetInviteTemplateAPIView.as_view(),
        name="getInviteTemplate",
    ),
    url(
        "v1/updatePlacidTemplates",
        UpdatePlacidTemplateView.as_view(),
        name="upate-placid-template"
    )
]
