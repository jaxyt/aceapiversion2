from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, SimpleCookie, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from pymongo import MongoClient
import re
import json
import datetime
import xml.etree.ElementTree as ET
from bson.json_util import dumps
# Create your views here.
from sites.models import Site
from templates.models import Template
from blogs.models import Blog
from states.models import State
from counties.models import County
from cities.models import City
from registeredagents.models import RegisteredAgent, TelecomCorps
from django.contrib.auth.models import User
from .forms import SiteForm, TemplateForm, BlogForm, StateForm, CountyForm, CityForm, RegisteredAgentForm, TelecomCorpsForm, UploadFileForm, RichForm
import os
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'registered_agents.json')


def compile_v4(request, *args, **kwargs):
    from .raclone import compiler_v4, render_xml_sitemap, replace_shortcodes
    site_id = request.GET.get('id', '2')
    route = request.GET.get('route', '/')
    page_uri_array = route.split('/')
    site = Site.objects.get(id=int(site_id))
    template = Template.objects.get(id=site.templateid)
    try:
        if re.search(r'sitemap(-[0-9]+)?\.xml$', route) is not None:
            compiled = render_xml_sitemap(site, template, route)
            response = HttpResponse("", content_type="application/xml; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'robots\.txt$', route) is not None:
            compiled = create_robots(site)
            response = HttpResponse("", content_type="text/plain; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.xml$', route) is not None:
            compiled = determine_page(route, site, template)
            response = HttpResponse("", content_type="application/xml; charset=utf-8")
            response.write(compiled)
        elif re.search(r'\.css$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="text/css; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.js$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="text/javascript; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.sch$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/ld+json; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.json$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/json; charset=utf-8")
            response.write(compiled)
            return response
        if re.search(r'\.ppp$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/x-httpd-php; charset=utf-8")
            response.write(compiled)
            return response
        else:
            compiled = compiler_v4(site, template, route, page_uri_array)
            return HttpResponse(compiled, content_type="text/html")
    except Exception as e:
        print(e)
        return HttpResponse("<h1>This Page Does Not Exist</h1><br><a href='/'>Return Home</a>", content_type="text/html")


def test_send(request):
    from .mongo_functions import compiler_v3, render_xml_sitemap, replace_shortcodes
    site_id = request.GET.get('id', '2')
    route = request.GET.get('route', '/')
    page_uri_array = route.split('/')
    site = Site.objects.get(id=int(site_id))
    template = Template.objects.get(id=site.templateid)
    try:
        if re.search(r'sitemap(-[0-9]+)?\.xml$', route) is not None:
            compiled = render_xml_sitemap(site, template, route)
            response = HttpResponse("", content_type="application/xml; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'robots\.txt$', route) is not None:
            compiled = create_robots(site)
            response = HttpResponse("", content_type="text/plain; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.xml$', route) is not None:
            compiled = determine_page(route, site, template)
            response = HttpResponse("", content_type="application/xml; charset=utf-8")
            response.write(compiled)
        elif re.search(r'\.css$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="text/css; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.js$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="text/javascript; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.sch$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/ld+json; charset=utf-8")
            response.write(compiled)
            return response
        elif re.search(r'\.json$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/json; charset=utf-8")
            response.write(compiled)
            return response
        if re.search(r'\.ppp$', route) is not None:
            compiled = determine_page(route, site, template)
            compiled = replace_shortcodes(site, template, compiled)
            response = HttpResponse("", content_type="application/x-httpd-php; charset=utf-8")
            response.write(compiled)
            return response
        else:
            compiled = compiler_v3(site, template, route, page_uri_array)
            return HttpResponse(compiled, content_type="text/html")
    except Exception as e:
        print(e)
        return HttpResponse("<h1>This Page Does Not Exist</h1><br><a href='/'>Return Home</a>", content_type="text/html")

def handle_uploaded_file(f, t):
    with open(os.path.join(module_dir, t), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def determine_page(rt, s, t):
    spage = None
    tpage = None
    cont = ""
    for i in s.pages:
        if i.route == rt:
            spage = i
    for i in t.pages:
        if i.route == rt:
            tpage = i
    cont += spage.content if spage.content else tpage.content if tpage.content else ""
    return cont


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            filename = request.POST.get('title')
            handle_uploaded_file(request.FILES['file'], filename)
            return HttpResponseRedirect('/auth/manage/')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def home(request, *args, **kwargs):
    print(request.headers)
    return HttpResponse("Hello World")

def login(request, *args, **kwargs):
    return render(request, 'login.html')

def manage(request, *args, **kwargs):
    if request.COOKIES.get('sessionid'):
        sites = Site.objects.all()
        templates = Template.objects.all()
        blogs = Blog.objects.all()
        states = State.objects.all()
        updatesites = ""
        for i in sites:
            updatesites += """<a href="/auth/site/update/?id={}">{}: {}</a>""".format(i.id, i.id, i.sitename)

        updatetemplates = ""
        for i in templates:
            updatetemplates += """<a href="/auth/template/update/?id={}">{}: {}</a>""".format(i.id, i.id, i.templatename)

        updateblogs = ""
        for i in blogs:
            updateblogs += """<a href="/auth/blog/update/?id={}">{}: {}</a>""".format(i.id, i.id, i.blogtitle)

        updatestates = ""
        for i in states:
            updatestates += """<a href="/auth/state/update/?id={}">{}: {}</a>""".format(i.id, i.id, i.statename)
            
        context = {
            'sites': updatesites,
            'templates': updatetemplates,
            'blogs': updateblogs,
            'states': updatestates
        }
        return render(request, 'manage.html', context)
    else:
        return HttpResponse('FORBIDDEN')

def create_xml_sitemap(site):
    compiled = """<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for i in site.pages:
        if i.route == "/locations/state":
            if site.national == True:
                states = State.objects.mongo_aggregate([{'$project': {"state": "$statename"}}])
                for n in states:
                    compiled += f"""<url><loc>https://www.{site.sitename}.com/locations/{"-".join(n["state"].split(" "))}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
            else:
                compiled += f"""<url><loc>https://www.{site.sitename}.com/locations/{"-".join(site.location.statename.split(" "))}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
        elif i.route == "/locations/state/county":
            if site.national == False:
                counties = County.objects.filter(stateid=site.location.stateid)
                for n in counties:
                    compiled += f"""<url><loc>https://www.{site.sitename}.com/locations/{"-".join(n.statename.split(" "))}/{"-".join(n.countyname.split(" "))}-{n.id}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
            else:
                compiled += ""
        elif i.route == "/locations/state/county/city":
            if site.national == True:
                cities = City.objects.mongo_aggregate(
                    [{'$project': {"id": "$id", "county": "$countyname", "cid":"$countyid", "state": "$statename", "city":"$cityname"}}])
                for n in cities:
                    compiled += f"""<url><loc>https://www.{site.sitename}.com/locations/{"-".join(n["state"].split(" "))}/{"-".join(n["county"].split(" "))}-{n["cid"]}/{"-".join(n["city"].split(" "))}-{n["id"]}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
            else:
                cities = City.objects.filter(stateid=site.location.stateid)
                for n in cities:
                    compiled += f"""<url><loc>https://www.{site.sitename}.com/locations/{"-".join(n.statename.split(" "))}/{"-".join(n.countyname.split(" "))}-{n.countyid}/{"-".join(n.cityname.split(" "))}-{n.id}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
        elif i.route == "/blog/posts/id":
            blogposts = Blog.objects.filter(blogcategory=site.blogcategory)
            for n in blogposts:
                compiled += f"""<url><loc>https://www.{site.sitename}.com/blog/posts/{"-".join(n.bloguri.split(" "))}-{n.id}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
        else:
            compiled += f"""<url><loc>https://www.{site.sitename}.com{i.route}</loc><lastmod>{datetime.date.today()}</lastmod></url>"""
    compiled += "</urlset>"
    return compiled

def create_robots(site):
    robots = """
    User-Agent: *

    Disallow: 

    Sitemap: https://www.{}.com/sitemap.xml
    """.format(site.sitename)
    return robots


def compile_page(site, route, uri_arr):
    page = route
    spage = None
    tpage = None
    states = State.objects.all()
    site_state = State.objects.get(id=site.location.stateid) if site.location.stateid else ""
    site_county = County.objects.get(id=site.location.countyid) if site.location.countyid else ""
    site_city = City.objects.get(id=site.location.cityid) if site.location.cityid else ""
    site_counties_in_state = County.objects.filter(stateid=site.location.stateid) if site.location.stateid else ""
    site_cities_in_state = City.objects.filter(stateid=site.location.stateid) if site.location.stateid else ""
    site_cities_in_county = City.objects.filter(countyid=site.location.countyid) if site.location.countyid else ""
    page_state = None
    page_county = None
    page_city = None
    page_counties_in_state = None
    page_cities_in_state = None
    page_cities_in_county = None

    states_list = ""
    site_counties_in_state_list = ""
    site_cities_in_state_list = ""
    site_cities_in_county_list = ""
    page_counties_in_state_list = ""
    page_cities_in_state_list = ""
    page_cities_in_county_list = ""

    for i in states:
        states_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.id}">{i.statename.title()}</a>"""
    for i in site_counties_in_state:
        site_counties_in_state_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.id}">{i.countyname.title()}</a>"""
    for i in site_cities_in_state:
        site_cities_in_state_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.countyid}/{"-".join(i.cityname.split(" "))}-{i.id}">{i.cityname.title()}</a>"""
    for i in site_cities_in_county:
        site_cities_in_county_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.countyid}/{"-".join(i.cityname.split(" "))}-{i.id}">{i.cityname.title()}</a>"""

    blogpost = None
    blog = Blog.objects.filter(blogcategory=site.blogcategory) if site.blogcategory else ""
    blog_post_snippets = ""
    for i in blog:
        blog_post_snippets += f"""<div><h2><a href="/blog/posts/{"-".join(i.bloguri.split(" ")) if i.bloguri else ""}-{i.id}">{i.blogtitle}</a></h2><p>{i.blogpost[0:100] if len(i.blogpost) > 100 else i.blogpost}...</p></div>"""
    template = Template.objects.get(id=site.templateid)
    if uri_arr[1] == "locations" and len(uri_arr) > 2:
        if len(uri_arr) == 3:
            page = "/locations/state"
        elif len(uri_arr) == 4:
            page = "/locations/state/county"
        elif len(uri_arr) == 5:
            page = "/locations/state/county/city"

        page_state = State.objects.get(id=int(uri_arr[2].split("-")[-1]))
        page_counties_in_state = County.objects.filter(stateid=page_state.id)
        page_cities_in_state = City.objects.filter(stateid=page_state.id)

        for i in page_counties_in_state:
            page_counties_in_state_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.id}">{i.statename.title()}</a>"""
        for i in page_cities_in_state:
            page_cities_in_state_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.countyid}/{"-".join(i.cityname.split(" "))}-{i.id}">{i.cityname.title()}</a>"""
        if len(uri_arr) > 3:
            page_county = County.objects.get(id=int(uri_arr[3].split("-")[-1]))
            page_cities_in_county = City.objects.filter(countyid=page_county.id)
            for i in page_cities_in_county:
                page_cities_in_county_list += f"""<a href="/locations/{"-".join(i.statename.split(" "))}-{i.stateid}/{"-".join(i.countyname.split(" "))}-{i.countyid}/{"-".join(i.cityname.split(" "))}-{i.id}">{i.cityname.title()}</a>"""
            if len(uri_arr) > 4:
                page_city = City.objects.get(id=int(uri_arr[4].split("-")[-1]))
    elif uri_arr[1] == "blog" and uri_arr[2] == "posts":
        if len(uri_arr) == 3:
            page = "/blog/posts"
        elif len(uri_arr) == 4:
            page = "/blog/posts/id"
            blogpost = Blog.objects.get(id=uri_arr[-1].split("-")[-1])

    for i in site.pages:
        if i.route == page:
            spage = i
    for i in template.pages:
        if i.route == page:
            tpage = i

    compiled = """<!DOCTYPE html>
<html>
    <head>
    """
    compiled += f"""<!--meta-->{site.sitemetas if site.sitemetas else (template.sitemetas if template.sitemetas else "")}{spage.pagemetas if spage.pagemetas else (tpage.pagemetas if tpage.pagemetas else "")}{("<meta name='keywords' content='" + blogpost.keywords + "' />") if blogpost else ""}"""
    compiled += f"""<!--link-->{site.sitelinks if site.sitelinks else (template.sitelinks if template.sitelinks else "")}{spage.pagelinks if spage.pagelinks else (tpage.pagelinks if tpage.pagelinks else "")}"""
    compiled += f"""<title>{spage.title if spage.title else (tpage.title if tpage.title else "")}</title>"""
    compiled += f"""<!--style--><style>{spage.pagestyle if spage.pagestyle else (site.sitestyle if site.sitestyle else (tpage.pagestyle if tpage.pagestyle else (template.sitestyle if template.sitestyle else "")))}</style>"""
    compiled += """
    </head>
    <body>
    """
    compiled += f"""<!--header-->{spage.pageheader if spage.pageheader else (site.siteheader if site.siteheader else (tpage.pageheader if tpage.pageheader else (template.siteheader if template.siteheader else "")))}"""
    compiled += f"""<!--content-->{spage.content if spage.content else (tpage.content if tpage.content else "")}"""
    compiled += f"""<!--footer-->{spage.pagefooter if spage.pagefooter else (site.sitefooter if site.sitefooter else (tpage.pagefooter if tpage.pagefooter else (template.sitefooter if template.sitefooter else "")))}"""
    compiled += f"""<!--script-->{site.sitescripts if site.sitescripts else (template.sitescripts if template.sitescripts else "")}{spage.pagescripts if spage.pagescripts else (tpage.pagescripts if tpage.pagescripts else "")}"""
    compiled += """
    </body>
</html>
    """
    compiled = re.sub("XXstateslistXX", states_list, compiled)
    compiled = re.sub("XXstateXX", site_state.statename.title(), compiled)
    compiled = re.sub("XXcountyXX", site_county.countyname.title(), compiled)
    compiled = re.sub("XXcityXX", site_city.cityname.title(), compiled)
    compiled = re.sub("XXcountiesstateXX", site_counties_in_state_list, compiled)
    compiled = re.sub("XXcitiesinstateXX", site_cities_in_state_list, compiled)
    compiled = re.sub("XXcitiesincountyXX", site_cities_in_county_list, compiled)
    compiled = re.sub("XXblogpostsnippetsXX", blog_post_snippets, compiled)

    if uri_arr[1] == "locations" and len(uri_arr) > 2:
        if len(uri_arr) == 3:
            compiled = re.sub("XXpagestateXX", page_state.statename.title(), compiled)
            compiled = re.sub("XXpagecountiesinstateXX", page_counties_in_state_list, compiled)
            compiled = re.sub("XXpagecitiesinstateXX", page_cities_in_state_list, compiled)
        elif len(uri_arr) == 4:
            compiled = re.sub("XXpagestateXX", page_state.statename.title(), compiled)
            compiled = re.sub("XXpagecountiesinstateXX", page_counties_in_state_list, compiled)
            compiled = re.sub("XXpagecitiesinstateXX", page_cities_in_state_list, compiled)
            compiled = re.sub("XXpagecountyXX", page_county.countyname.title(), compiled)
            compiled = re.sub("XXpagecitiesincountyXX", page_cities_in_county_list, compiled)
        elif len(uri_arr) == 5:
            compiled = re.sub("XXpagestateXX", page_state.statename.title(), compiled)
            compiled = re.sub("XXpagecountiesinstateXX", page_counties_in_state_list, compiled)
            compiled = re.sub("XXpagecitiesinstateXX", page_cities_in_state_list, compiled)
            compiled = re.sub("XXpagecountyXX", page_county.countyname.title(), compiled)
            compiled = re.sub("XXpagecitiesincountyXX", page_cities_in_county_list, compiled)
            compiled = re.sub("XXpagecityXX", page_city.cityname.title(), compiled)
    elif uri_arr[1] == "blog" and uri_arr[2] == "posts":
        if len(uri_arr) == 3:
            wut = ""
        else:
            local_blog = f"""
                        <div><h1>{blogpost.blogtitle}</h1><p>{blogpost.blogpost}</p></div>"""
            national_blog  = f"""<div><h1>{blogpost.blogtitle}</h1><p>{blogpost.blogpost}</p></div>"""
            compiled = re.sub("XXblogpostXX", local_blog, compiled)
            compiled = re.sub("XXblogpostnationalXX", national_blog, compiled)
            compiled = re.sub("XXblogtitleXX", blogpost.blogtitle, compiled)

    for i in site.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    
    for i in site.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = re.compile(f"""XX{i.name}XX""")
        compiled = re.sub(reg, i.value, compiled)

    return compiled


def send_page(request, *args, **kwargs):
    try:
        site_id = request.GET.get('id', '')
        route = request.GET.get('route', '')
        page_uri_array = route.split("/")
        site = Site.objects.get(id=int(site_id))
        if re.search(r"sitemap[0-9]?\.xml$", page_uri_array[-1]):
            sitemap = create_xml_sitemap(site)
            return HttpResponse(sitemap, content_type="application/xml")
        elif re.search(r"robots\.txt$", page_uri_array[-1]):
            robots = create_robots(site)
            return HttpResponse(robots, content_type="text/plain")
        else:
            compiled = compile_page(site, route, page_uri_array)
            return HttpResponse(compiled, content_type="text/html")
    except AttributeError as e:
        print(e)
        raise Http404

def compile(request, *args, **kwargs):
    id = request.GET.get('id', '')
    route = request.GET.get('route', '')
    pageroute = route
    pageURIArray = route.split('/')
    blogpost = None
    if len(pageURIArray) > 2:
        if pageURIArray[1] == "locations":
            if len(pageURIArray) == 3:
                pageroute = "/locations/state"
            elif len(pageURIArray) == 4:
                pageroute = "/locations/state/county"
            elif len(pageURIArray) == 5:
                pageroute = "/locations/state/county/city"
        elif pageURIArray[1] == "blog":
            if len(pageURIArray) == 4 and pageURIArray[2] == "posts":
                pageroute = "/blog/posts/id"
                postid = pageURIArray[3].split('-')
                blogpost = Blog.objects.get(id=postid[-1])
    site = Site.objects.get(id=int(id))
    template = Template.objects.get(id=site.templateid)
    spage = None
    tpage = None
    for i in site.pages:
        if i.route == pageroute:
            spage = i
    for i in template.pages:
        if i.route == pageroute:
            tpage = i
    if pageroute == "/sitemap.xml":
        sitemap = create_xml_sitemap(site)
        return HttpResponse(sitemap, content_type="application/xml")
    if pageroute == "/robots.txt":
        robots = create_robots(site)
        return HttpResponse(robots, content_type="text/plain")
    if re.search(r'\.ppp$', route) is not None:
        from .mongo_functions import replace_shortcodes
        compiled = determine_page(route, site, template)
        compiled = replace_shortcodes(site, template, compiled)
        response = HttpResponse("", content_type="application/x-httpd-php; charset=utf-8")
        response.write(compiled)
        return response
    compiled = """
    <!DOCTYPE html>
    <html lang="eng">
    <head>
    """
    compiled += site.sitemetas if site.sitemetas else (template.sitemetas if template.sitemetas else "")
    compiled += spage.pagemetas if spage.pagemetas else (tpage.pagemetas if tpage.pagemetas else "")
    compiled += f"""<meta name="keywords" content="{blogpost.blogkeywords}" />""" if blogpost else ""

    compiled += site.sitelinks if site.sitelinks else (template.sitelinks if template.sitelinks else "")
    compiled += spage.pagelinks if spage.pagelinks else (tpage.pagelinks if tpage.pagelinks else "")

    compiled += """
    <title>
    """
    compiled += spage.title if spage.title else (tpage.title if tpage.title else "")
    compiled += """
    </title>
    """

    compiled += """
    <style>
    """
    # compiled += site.sitestyle if site.sitestyle else (template.sitestyle if template.sitestyle else "")
    # compiled += spage.pagestyle if spage.pagestyle else (tpage.pagestyle if tpage.pagestyle else "")
    compiled += spage.pagestyle if spage.pagestyle else (site.sitestyle if site.sitestyle else (tpage.pagestyle if tpage.pagestyle else (template.sitestyle if template.sitestyle else "")))
    compiled += """
    </style>
    </head>
    <body>
    <div id="grid">
    """

    compiled += spage.pageheader if spage.pageheader else (site.siteheader if site.siteheader else (tpage.pageheader if tpage.pageheader else (template.siteheader if template.siteheader else "")))

    compiled += spage.content if spage.content else (tpage.content if tpage.content else "")

    compiled += spage.pagefooter if spage.pagefooter else (site.sitefooter if site.sitefooter else (tpage.pagefooter if tpage.pagefooter else (template.sitefooter if template.sitefooter else "")))
    compiled += "</div>"
    compiled += site.sitescripts if site.sitescripts else (template.sitescripts if template.sitescripts else "")
    compiled += spage.pagescripts if spage.pagescripts else (tpage.pagescripts if tpage.pagescripts else "")
    compiled += """
    </body>
    </html>
    """

    for i in site.shortcodes:
        reg = f"""XX{i.name}XX"""
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = f"""XX{i.name}XX"""
        compiled = re.sub(reg, i.value, compiled)

    statelist = State.objects.all()
    statelinks = ""
    for i in statelist:
        statelinks += f"""<a href="/locations/{"-".join(i.statename.split(' '))}">{i.statename.title()}</a>"""
    compiled = re.sub("XXstatelinksXX", statelinks, compiled)

    state = State.objects.get(id=site.location.stateid) if State.objects.get(id=site.location.stateid) else ""
    compiled = re.sub("XXstateXX", state.statename.title(), compiled)
    county = County.objects.get(id=site.location.countyid) if County.objects.get(id=site.location.countyid) else ""
    compiled = re.sub("XXcountyXX", county.countyname.title(), compiled)
    city = City.objects.get(id=site.location.cityid) if City.objects.get(id=site.location.cityid) else ""
    compiled = re.sub("XXcityXX", city.cityname.title(), compiled)
    sitecounties = County.objects.filter(stateid=state.id) if County.objects.filter(stateid=state.id) else []
    sitecities = City.objects.filter(countyid=county.id) if City.objects.filter(countyid=county.id) else []
    sitecitiesinstate = City.objects.filter(stateid=state.id) if City.objects.filter(stateid=state.id) else []
    sitecountylinks = ""
    sitecitylinks = ""
    sitecitiesinstatelinks = ""
    for i in sitecounties:
        sitecountylinks += f"""<a href="/locations/{"-".join(i.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.id}">{i.countyname.title()}</a>"""
    compiled = re.sub("XXsitecountylinksXX", sitecountylinks, compiled)
    for i in sitecitiesinstate:
        sitecitiesinstatelinks += f"""<a href="/locations/{"-".join(i.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.countyid}/{"-".join(i.cityname.split(' '))}-{i.id}">{i.cityname.title()}</a>"""
    compiled = re.sub("XXsitecitiesinstatelinksXX", sitecitiesinstatelinks, compiled)
    for i in sitecities:
        sitecitylinks += f"""<a href="/locations/{"-".join(i.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.countyid}/{"-".join(i.cityname.split(' '))}-{i.id}">{i.cityname.title()}</a>"""
    compiled = re.sub("XXsitecitylinksXX", sitecitylinks, compiled)

    pagestate = ""
    pagecounty = ""
    pagecity = ""
    pagecounties = None
    pagecities = None
    pagecitiesinstate = None
    pagecountylinks = ""
    pagecitylinks = ""
    pagecitiesinstatelinks = ""
    if len(pageURIArray) > 2:
        if pageURIArray[1] == "locations":
            if len(pageURIArray) > 2:
                pagestate = State.objects.get(statename=" ".join(pageURIArray[2].split('-')))
                pagecounties = County.objects.filter(stateid=pagestate.id) if County.objects.filter(stateid=pagestate.id) else []
                pagecitiesinstate = City.objects.filter(stateid=pagestate.id) if City.objects.filter(stateid=pagestate.id) else []
                compiled = re.sub("XXpagestateXX", pagestate.statename.title(), compiled)
                for i in pagecounties:
                    pagecountylinks += f"""<a href="/locations/{"-".join(pagestate.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.id}">{i.countyname.title()}</a>"""
                compiled = re.sub("XXpagecountylinksXX", pagecountylinks, compiled)
                for i in pagecitiesinstate:
                    pagecitiesinstatelinks += f"""<a href="/locations/{"-".join(pagestate.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.countyid}/{"-".join(i.cityname.split(' '))}-{i.id}">{i.cityname.title()}</a>"""
                compiled = re.sub("XXpagecitiesinstatelinksXX", pagecitiesinstatelinks, compiled)
                if len(pageURIArray) > 3:
                    pagecounty = County.objects.get(id=int(pageURIArray[3].split('-')[-1]))
                    compiled = re.sub("XXpagecountyXX", pagecounty.countyname.title(), compiled)
                    pagecities = City.objects.filter(countyid=pagecounty.id) if City.objects.filter(countyid=pagecounty.id) else []
                    for i in pagecities:
                        pagecitylinks += f"""<a href="/locations/{"-".join(pagestate.statename.split(' '))}/{"-".join(i.countyname.split(' '))}-{i.countyid}/{"-".join(i.cityname.split(' '))}-{i.id}">{i.cityname.title()}</a>"""
                    compiled = re.sub("XXpagecitylinksXX", pagecitylinks, compiled)
                    if len(pageURIArray) > 4:
                        pagecity = City.objects.get(id=int(pageURIArray[4].split('-')[-1]))
                        compiled = re.sub("XXpagecityXX", pagecity.cityname.title(), compiled)
        elif pageURIArray[1] == "blog" and len(pageURIArray) == 4:
            blogbody = remove_html_tags(blogpost.blogpost)
            blogbody = re.sub(r"\r\n", " ", blogbody)
            blogbody = re.sub('"', '&quot;', blogbody)
            blogbody = re.sub("'", "&apos;", blogbody)
            singleblog = """
            <div>
            <h1 id="blogtitle">{0}</h1>
            <div><strong>Last updated:</strong>&nbsp;<span class="datetime">{1}</span></div>
            <div id="blogpostcontent">{2}</div>
            </div>
            <script type="application/ld+json">
            {10} "@context": "https://schema.org",
              "@type": "BlogPosting",
              "headline": "{0}",
              "genre": "{8}",
              "keywords": "{9}",
              "wordcount": "{4}",
              "url": "https://www.{5}.com/blog/posts/{6}-{7}",
              "dateModified": "{1}",
              "articleBody": "{3}",
              "author": {10}
                "@type": "Person",
                "name": "{12}"
              {11}
             {11}
            </script>
            """.format(blogpost.blogtitle, blogpost.blogdate.astimezone().strftime('%m-%d-%Y %H:%M:%S'), blogpost.blogpost, blogbody, len(blogbody.split(' ')), site.sitename, blogpost.bloguri, blogpost.id, blogpost.blogcategory, blogpost.blogkeywords, '{', '}', blogpost.blogauthor)
            compiled = re.sub("XXblogpostXX", singleblog, compiled)
            blogbodynational = remove_html_tags(blogpost.blogpostnational)
            blogbodynational = re.sub(r"\r\n", " ", blogbodynational)
            blogbodynational = re.sub('"', '&quot;', blogbodynational)
            blogbody = re.sub("'", "&apos;", blogbodynational)
            singleblognational = """
            <div>
            <h1 id="blogtitle">{0}</h1>
            <div><strong>Last updated:</strong>&nbsp;<span class="datetime">{1}</span></div>
            <div id="blogpostcontent">{2}</div>
            </div>
            <script type="application/ld+json">
            {10} "@context": "https://schema.org",
              "@type": "BlogPosting",
              "headline": "{0}",
              "genre": "{8}",
              "keywords": "{9}",
              "wordcount": "{4}",
              "url": "https://www.{5}.com/blog/posts/{6}-{7}",
              "dateModified": "{1}",
              "articleBody": "{3}",
              "author": {10}
                "@type": "Person",
                "name": "{12}"
              {11}
              {11}
            </script>
            """.format(blogpost.blogtitle, blogpost.blogdate.astimezone().strftime('%m-%d-%Y %H:%M:%S'), blogpost.blogpostnational, blogbodynational, len(blogbodynational.split(' ')), site.sitename, blogpost.bloguri, blogpost.id, blogpost.blogcategory, blogpost.blogkeywords, '{', '}', blogpost.blogauthor)
            compiled = re.sub("XXblogpostnationalXX", singleblognational, compiled)
    blogposts = Blog.objects.filter(blogcategory=site.blogcategory) if Blog.objects.filter(blogcategory=site.blogcategory) else []
    blogpostsnippets = ""
    for i in blogposts:
        blogpostsnippets += f"""<div><h2><a href="/blog/posts/{"-".join(i.bloguri.split(" ")) if i.bloguri else ""}-{i.id}">{i.blogtitle}</a></h2><p>{i.blogpost[0:100] if len(i.blogpost) > 100 else i.blogpost}...</p></div>"""
    compiled = re.sub("XXblogpostsnippetsXX", blogpostsnippets, compiled)
    compiled = re.sub("XXstateXX", state.statename.title(), compiled)
    compiled = re.sub("XXcountyXX", county.countyname.title(), compiled)
    compiled = re.sub("XXcityXX", city.cityname.title(), compiled)

    for i in site.shortcodes:
        reg = f"""XX{i.name}XX"""
        compiled = re.sub(reg, i.value, compiled)
    for i in template.shortcodes:
        reg = f"""XX{i.name}XX"""
        compiled = re.sub(reg, i.value, compiled)

    return HttpResponse(compiled)


def create_site(request):
    if request.COOKIES.get('sessionid'):
        form = SiteForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = SiteForm()

        context = {
            'form': form
        }

        return render(request, "site.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_site(request):
    if request.COOKIES.get('sessionid'):

        id = request.GET.get('id', '')
        instance = get_object_or_404(Site, id=id)
        form = SiteForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "site.html", context)
    else:
        return HttpResponse('FORBIDDEN')



def create_template(request):
    if request.COOKIES.get('sessionid'):
        form = TemplateForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = TemplateForm()

        context = {
            'form': form
        }

        return render(request, "template.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_template(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(Template, id=id)
        form = TemplateForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "template.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def create_blog(request):
    if request.COOKIES.get('sessionid'):
        form = BlogForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = BlogForm()

        context = {
            'form': form
        }

        return render(request, "blog.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_blog(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(Blog, id=id)
        form = BlogForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "blog.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def create_state(request):
    if request.COOKIES.get('sessionid'):
        form = StateForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = StateForm()

        context = {
            'form': form
        }

        return render(request, "state.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_state(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(State, id=id)
        form = StateForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        counties = County.objects.filter(stateid=id)
        countycreate = """<a href="/auth/county/create/?state={}">create a new county in {}</a>""".format(id,
                                                                                                     instance.statename)
        countylist = ""
        for i in counties:
            countylist += """<a href="/auth/county/update/?id={}">{}: {}</a>""".format(i.id, i.id, i.countyname)

        cities = City.objects.filter(stateid=id)
        citycreatelist = ""
        for i in counties:
            citycreatelist += """<a href="/auth/city/create/?state={}&county={}">{}: {}<a>""".format(
                i.stateid, i.id, i.id, i.countyname)

        citylist = ""
        for i in cities:
            citylist += """<a href="/auth/city/update/?id={}">{}: {}; {}: {}; {}: {}</a>""".format(i.id, i.id, i.cityname, i.countyid, i.countyname, i.stateid, i.statename)

        context = {
            'form': form,
            'countycreate': countycreate,
            'citycreatelist': citycreatelist,
            'citylist': citylist,
        }

        return render(request, "state.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def create_county(request):
    if request.COOKIES.get('sessionid'):
        form = CountyForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = CountyForm()

        stateid = request.GET.get('state', '')
        state = State.objects.get(id=stateid)
        sid = state.id
        sname = state.statename

        context = {
            'form': form,
            'sid': sid,
            'sname': sname,
        }

        return render(request, "county.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_county(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(County, id=id)
        form = CountyForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "county.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def create_city(request):
    if request.COOKIES.get('sessionid'):
        state = request.GET.get('state', '')
        county = request.GET.get('county', '')
        citystate = State.objects.get(id=state)
        citycounty = County.objects.get(id=county)
        form = CityForm(request.POST or None)
        if form.is_valid():
            form.save()
            form = CityForm()

        context = {
            'form': form,
            'stateid': citystate.id,
            'statename': citystate.statename,
            'countyid': citycounty.id,
            'countyname': citycounty.countyname
        }

        return render(request, "city.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_city(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(City, id=id)
        form = CityForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "city.html", context)
    else:
        return HttpResponse('FORBIDDEN')


"""
def insertallcountiesinstate(request):
    stateid = 1
    statename = 'florida'
    counties = []
    for i in counties:
        newcounty = {
            'stateid': stateid,
            'statename': statename,
            'countyname': i
        }
        form = CountyForm(newcounty)
        form.save()
    return HttpResponse("complete")
"""

"""
def makedb3(request):
    statecnt = int(request.GET.get('state', ''))
    countycnt = int(request.GET.get('county', ''))
    citycnt = int(request.GET.get('city', ''))
    state_id = request.GET.get('id', '')
    with open(file_path) as json_file:
        data = json.load(json_file)
        i = data[int(state_id)]
        state_obj = {
            'statename': i['statename']
        }
        state_form = StateForm(state_obj)
        state_form.save()
        for n in i['countiesinstate']:
            county_obj = {
                'stateid': statecnt,
                'statename': i['statename'],
                'countyname': n['countyname']
            }
            county_form = CountyForm(county_obj)
            county_form.save()
            for k in n['citiesincounty']:
                city_obj = {
                    'stateid': statecnt,
                    'statename': i['statename'],
                    'countyid': countycnt,
                    'countyname': n['countyname'],
                    'cityname': k
                }
                city_form = CityForm(city_obj)
                city_form.save()
                citycnt += 1
            countycnt += 1
        return HttpResponse("complete")
"""

def make_ngrams(word, min_size=2):
    """
    basestring       word: word to split into ngrams
           int   min_size: minimum size of ngrams
    """
    length = len(word)
    size_range = range(min_size, max(length, min_size) + 1)
    return list(set(
        word[i:i + size]
        for size in size_range
        for i in range(0, max(0, length - size) + 1)
    ))

def getlocations(request):
    query = request.GET.get('q', '').strip('"')
    cities = City.objects.mongo_aggregate( [ { '$project': { 'city': "$cityname" } } ] )
    counties = County.objects.mongo_aggregate( [ { '$project': { 'county': "$countyname" } } ] )
    states = State.objects.mongo_aggregate( [ { '$project': { 'state': "$statename" } } ] )
    q = make_ngrams(query)
    return HttpResponse(query)


def addngrams(request):
    """
    stateid = request.GET.get('id', '')
    cities = City.objects.mongo_aggregate([{'$match': {'stateid': int(stateid)}}, { '$project': { 'city': { '$concat': [ "$cityname","$statename" ] }, 'id': "$id" }}])
    seagrams = []
    for i in cities:
       city_update = {
         'cid': i['id'],
         'cgram': make_ngrams(re.sub(" ", "", i['city']))
       }
       seagrams.append(city_update)
    for n in seagrams:
      city = City.objects.get(id=n['cid'])
      city.cityngram = " ".join(n['cgram'])
      city.save(update_fields=["cityngram"])
    print("done")
    """
    mongo_client = MongoClient('mongodb://localhost:27017')
    db = mongo_client.acedbv2
    colstate = db.states_state
    colcounty = db.counties_county
    colcity = db.cities_city
    """
    colstate.create_index(
      [
        ("statengram", "text"),
      ],
      name="search_state_ngrams",
      weights={
        "statengram": 100,
      }
    )
    colcounty.create_index([("countyngram","text")],name="search_county_ngrams",weights={"countyngram": 100})
    colcity.create_index([("cityngram","text")],name="search_city_ngrams",weights={"cityngram": 100})
    """
    query = re.sub(" ", "", request.GET.get('q',''))
    results = colcity.find(
        {
            "$text": {
                "$search": query
            }
        },
        {
            "id": True,
            "_id": False,
            "statename": True,
            "countyid": True,
            "countyname": True,
            "cityname": True,
            "score": {
                "$meta": "textScore"
            }
        }
    ).sort([("score", {"$meta": "textScore"})])
    res = [doc for doc in results]
    return HttpResponse(json.dumps(res), content_type="application/json")


def json_to_mongo(request):
    md = os.path.dirname(__file__)
    fpath = os.path.join(md, "telecom.json")
    with open(fpath, "r+") as json_file:
        data = json.load(json_file)
        for idx, val in enumerate(data):
            if idx > 15068:
                form = TelecomCorpsForm(val)
                if form.is_valid():
                    form.save()
        return HttpResponse("complete", content_type="text/plain")

def add_cities_to_agents(request):
    md = os.path.dirname(__file__)
    fpath = os.path.join(md, "raloc.json")
    with open(fpath, "r+") as json_file:
        data = json.load(json_file)
        for i in data:
            agent = RegisteredAgent.objects.get(id=int(i['id']))
            agent.city = i['city']
            agent.save()
        return HttpResponse("complete", content_type="text/plain")


def get_registered_agents(request):
    from .mongo_functions import registered_agent_search
    ki = request.GET.get('k')
    val = request.GET.get('q')
    x = registered_agent_search(ki, val)
    return HttpResponse(x, content_type="text/plain")

def shee_exec(cmd):
    return os.popen(cmd).read()

@csrf_exempt
def pull_from_github(request):
    print("start")
    os.system("cd ~/ace/aceapiversion2/ && git pull")
    print("end")
    return HttpResponse('pong')



def update_editor(request):
    if request.COOKIES.get('sessionid'):
        id = request.GET.get('id', '')
        instance = get_object_or_404(Site, id=id)
        form = SiteForm(request.POST or None, instance=instance)
        if form.is_valid():
            form.save()

        context = {
            'form': form
        }

        return render(request, "editor.html", context)
    else:
        return HttpResponse('FORBIDDEN')


def update_nice(request):
    if request.COOKIES.get('sessionid'):
        form = RichForm()

        context = {
            'form': form
        }

        return render(request, "editor-niceadmin.html", context)
    else:
        return HttpResponse('FORBIDDEN')

