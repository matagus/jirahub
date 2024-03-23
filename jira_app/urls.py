from django.urls import path

from jira_app.views import (
    AccountDetailView,
    AccountListView,
    IssueListView,
    IssueDetailView,
    ProjectDetailView,
    SprintListView,
    ReleaseListView,
    BoardListView,
    BoardDetailView,
    CommentListView,
    HistoryListView,
    ChildIssueListView,
)


app_name = "jira_app"

urlpatterns = [
    path("", AccountListView.as_view(), name="account-list"),
    path("accounts/<slug:account_key>/", AccountDetailView.as_view(), name="account-detail"),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/", ProjectDetailView.as_view(), name="project-detail"
    ),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/sprints/", SprintListView.as_view(), name="sprint-list"
    ),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/releases/",
        ReleaseListView.as_view(),
        name="release-list",
    ),
    path("accounts/<slug:account_key>/projects/<slug:project_key>/boards/", BoardListView.as_view(), name="board-list"),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/boards/<int:board_id>/",
        BoardDetailView.as_view(),
        name="board-detail",
    ),
    path("accounts/<slug:account_key>/projects/<slug:project_key>/issues/", IssueListView.as_view(), name="issue-list"),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/issues/<slug:issue_key>/children/",
        ChildIssueListView.as_view(),
        name="children-list",
    ),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/issues/<slug:issue_key>/",
        IssueDetailView.as_view(),
        name="issue-detail",
    ),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/issues/<slug:issue_key>/comments/",
        CommentListView.as_view(),
        name="comment-list",
    ),
    path(
        "accounts/<slug:account_key>/projects/<slug:project_key>/issues/<slug:issue_key>/history/",
        HistoryListView.as_view(),
        name="history-list",
    ),
]
