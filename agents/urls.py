from django.urls import path, re_path
from .views import agent_create_and_list_view, compilerv4, upload_agents, AgentDeleteView, AgentUpdateView, home_view, get_static_page, blog_main, blog_post, abs_main, abs_state, abs_city, ps_agent, ps_state, ps_city, ra_search, ra_agent

app_name = 'agents'

urlpatterns = [
    path('', agent_create_and_list_view, name='main-agent-view'),
    #path('upload/', upload_agents, name='upload-agent-view'),
    path('compile/<int:siteid>/', home_view),
    path('compile/<int:siteid>/agents-by-state/', abs_main),
    path('compile/<int:siteid>/agents-by-state/<str:state>/', abs_state),
    path('compile/<int:siteid>/agents-by-state/<str:state>/<str:city>/', abs_city),
    path('compile/<int:siteid>/process-server/<str:agent>/', ps_agent),
    path('compile/<int:siteid>/process-server/<str:agent>/<str:state>/', ps_state),
    path('compile/<int:siteid>/process-server/<str:agent>/<str:state>/<str:city>/', ps_city),
    path('compile/<int:siteid>/registered-agents/search/<str:query>/', ra_search),
    path('compile/<int:siteid>/registered-agents/<str:agent>--<str:state>--<str:county>--<str:city>/<int:agentid>/', ra_agent),
    path('compile/<int:siteid>/blog/posts/', blog_main),
    path('compile/<int:siteid>/blog/posts/<str:blogtitle>-<int:blogid>/', blog_post),
    path('compile/<int:siteid>/<str:page>/', get_static_page),
    re_path(r"^compile/(?P<siteid>[\d]+)/.+$", home_view),

    #path('compile/<int:siteid>/', get_home, name='agent-home-view'),
    #path('compile/<int:siteid>/<str:page>/', compilerv5, name='agent-page-view'),
    #path('compile/<int:siteid>/<str:page>/posts/<slug:blog_title>-<int:blog_id>/', compilerv5, name='blog-search'),
    #path('compile/<int:siteid>/<str:page>/<str:agent>/<str:state>/<str:county>/<str:city>/<int:agentid>/', compilerv5, name='single-agent'),
    #path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/<str:arg_three>/<str:arg_four>/', compilerv5, name='agent-city'),
    #path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/<str:arg_three>/', compilerv5, name='acounty-or-city'),
    #path('compile/<int:siteid>/<str:page>/search/<str:arg_two>/', compilerv5, name='agent-search'),
    #path('compile/<int:siteid>/<str:page>/<str:arg_one>/<str:arg_two>/', compilerv5, name='astate-or-county'),
    #path('compile/<int:siteid>/<str:page>/<str:arg_one>/', compilerv5, name='agent-or-state'),
    path('<int:siteid>/', compilerv4, name='compile-site-view'),
    path('<pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
    path('<pk>/update/', AgentUpdateView.as_view(), name='agent-update'),
]
