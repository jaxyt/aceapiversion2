from django.urls import path
from .views import agent_create_and_list_view, compilerv4, compilerv5, get_home, upload_agents, AgentDeleteView, AgentUpdateView

app_name = 'agents'

urlpatterns = [
    path('', agent_create_and_list_view, name='main-agent-view'),
    #path('upload/', upload_agents, name='upload-agent-view'),
    
    path('compile/<int:siteid>/<str:page>/', compilerv5, name='agent-page-view'),
    path('compile/<int:siteid>/<str:page>/<str:agent>/<str:state>/<str:county>/<str:city>/<int:agentid>/', compilerv5, name='single-agent'),
    path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/<str:arg_three>/<str:arg_four>/', compilerv5, name='agent-city'),
    path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/<str:arg_three>/', compilerv5, name='acounty-or-city'),
    path('compile/<int:siteid>/<str:page>/search/<str:arg_two>/', compilerv5, name='agent-search'),
    path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/', compilerv5, name='astate-or-county'),
    path('compile/<int:siteid>/<str:page>/<str:arg_one>/', compilerv5, name='agent-or-state'),
    path('compile/<int:siteid>/', get_home, name='agent-home-view'),
    path('<int:siteid>/', compilerv4, name='compile-site-view'),
    path('<pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
    path('<pk>/update/', AgentUpdateView.as_view(), name='agent-update'),
]