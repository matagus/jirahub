from django.conf import settings
from django.http import Http404
from django.views.generic.base import TemplateView

from jira import JIRA
from jira.exceptions import JIRAError


class AccountListView(TemplateView):

    template_name = "jira_app/accounts/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["account_list"] = settings.ACCOUNT_MAP.values()

        return context


class AccountTemplateView(TemplateView):

    def _get_jac(self, account):
        return JIRA(account.url, basic_auth=(account.email, account.token))

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        account_key = kwargs.get("account_key")

        try:
            self.account = settings.ACCOUNT_MAP[account_key]
        except KeyError:
            raise Http404(f"Account {account_key} Not Found")

        self.jac = self._get_jac(self.account)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.account
        return context


class ProjectTemplateView(AccountTemplateView):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        project_key = kwargs.get("project_key")

        try:
            self.project = self.jac.project(project_key)
        except JIRAError:
            raise Http404("Project Not Found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context


class IssueListView(ProjectTemplateView):

    def get_template_names(self):
        if self.request.htmx.target:
            return ["jira_app/issues/partial_list.html"]

        return ["jira_app/issues/list.html"]

    def get(self, request, *args, **kwargs):

        group_by = request.GET.get("group-by") or "assignee"

        group_by_map = {
            "assignee": "assignee",
            "epic": "parent",
            "version": "fixVersion",
            "status": "status",
            "issuetype": "issuetype",
            "sprint": "sprint",
            "priority": "priority",
        }

        # never use user input values to build the JQL!
        group_by = group_by_map.get(group_by, "assignee")

        self.grouper_field = group_by

        jql_str = f'project="{self.project.key}"'

        try:
            sprint_id = int(request.GET.get("sprint"))
        except (ValueError, TypeError):
            sprint_id = None

        try:
            self.sprint = self.jac.sprint(sprint_id)

        except JIRAError:
            board_id = [b.id for b in self.jac.boards(projectKeyOrID=self.project.key)][0]
            sprint_list = self.jac.sprints(board_id)
            sprint_list.sort(key=lambda s: s.createdDate, reverse=True)
            self.sprint = sprint_list[0]

        try:
            release_id = int(request.GET.get("release"))
        except (ValueError, TypeError):
            release_id = None

        if release_id is not None:
            jql_str += f" AND fixVersion={release_id}"
        else:
            if sprint_id is not None:
                jql_str += f" AND sprint = {self.sprint.id}"

        self.release_id = release_id

        self.issue_list = self.jac.search_issues(
            jql_str + f" ORDER BY {group_by} ASC, updated DESC", maxResults=settings.MAX_RESULTS, expand="container"
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sprint"] = self.sprint
        context["release_id"] = self.release_id
        context["issue_list"] = self.issue_list
        context["grouper_field"] = self.grouper_field
        return context


class IssueDetailView(ProjectTemplateView):

    template_name = "jira_app/issues/detail.html"

    def get(self, request, *args, **kwargs):
        issue_key = kwargs["issue_key"]

        self.issue = self.jac.issue(issue_key, expand="renderedBody,renderedFields")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue"] = self.issue
        return context


class AccountDetailView(AccountTemplateView):

    template_name = "jira_app/accounts/detail.html"

    def get(self, request, *args, **kwargs):
        self.project_list = self.jac.projects()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_list"] = self.project_list
        return context


class ProjectDetailView(ProjectTemplateView):

    template_name = "jira_app/projects/detail.html"

    def get(self, request, *args, **kwargs):
        self.board_list = self.jac.boards(projectKeyOrID=self.project.key)

        release_list = []
        for r in self.jac.project_versions(self.project.key):
            unresolved = self.jac.version_count_unresolved_issues(r.id)
            r.count = self.jac.version_count_related_issues(r.id)["issuesFixedCount"]

            if r.count > 0:
                r.resolved = r.count - unresolved
                r.progress = int(float(r.resolved) / r.count * 100)
            else:
                r.resolved = 0
                r.progress = 0

            release_list.append(r)

        release_list.sort(key=lambda r: r.name, reverse=True)
        self.release_list = release_list

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["release_list"] = self.release_list
        context["board_list"] = self.board_list
        return context


class SprintListView(ProjectTemplateView):

    template_name = "jira_app/releases/list.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ReleaseListView(ProjectTemplateView):

    template_name = "jira_app/releases/list.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BoardListView(ProjectTemplateView):

    template_name = "jira_app/boards/list.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BoardDetailView(ProjectTemplateView):

    template_name = "jira_app/boards/detail.html"

    def get(self, request, *args, **kwargs):
        board_id = kwargs["board_id"]
        sprint_list = self.jac.sprints(board_id)
        sprint_list.sort(key=lambda s: s.createdDate, reverse=True)
        self.sprint_list = sprint_list

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sprint_list"] = self.sprint_list
        return context


class CommentListView(ProjectTemplateView):

    template_name = "jira_app/comments/list.html"

    def get(self, request, *args, **kwargs):
        issue_key = kwargs["issue_key"]

        self.issue = self.jac.issue(issue_key, expand="renderedBody,renderedFields")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue"] = self.issue
        return context

    def post(self, request, *args, **kwargs):
        issue_key = kwargs["issue_key"]
        comment = request.POST.get("comment")

        self.jac.add_comment(issue_key, comment)

        return self.get(request, *args, **kwargs)


class HistoryListView(ProjectTemplateView):

    template_name = "jira_app/history/list.html"

    def get(self, request, *args, **kwargs):
        issue_key = kwargs["issue_key"]

        self.issue = self.jac.issue(issue_key, expand="changelog")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue"] = self.issue
        context["fields_to_show"] = ["status", "assignee", "priority", "rank"]
        return context


class ChildIssueListView(ProjectTemplateView):

    template_name = "jira_app/issues/children_list.html"

    def get(self, request, *args, **kwargs):
        parent_key = kwargs["issue_key"]

        jql_str = f"project={self.project.key} AND parent={parent_key}"

        self.issue_list = self.jac.search_issues(
            jql_str + " ORDER BY status ASC, updated DESC", maxResults=settings.MAX_RESULTS, expand="container"
        )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["issue_list"] = self.issue_list
        context["level"] = int(self.request.GET.get("level", 0))
        return context
