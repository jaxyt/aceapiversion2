from django.urls import path
from .views import agent_create_and_list_view, compilerv4, upload_agents, AgentDeleteView, AgentUpdateView

app_name = 'agents'

urlpatterns = [
    path('', agent_create_and_list_view, name='main-agent-view'),
    path('', upload_agents, name='main-agent-view'),
    path('<int:siteid>/', compilerv4, name='compile-site-view'),
    path('<pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
    path('<pk>/update/', AgentUpdateView.as_view(), name='agent-update'),
]