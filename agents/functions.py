from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
import urllib.parse
from pymongo import MongoClient
import re
import os
import json
from django.template.defaultfilters import slugify
import linecache
import sys

client = MongoClient('mongodb://localhost:27017/')
db = client.acedbv2
coll_ra = db.agents_agent
coll_si = db.sites_site
coll_te = db.templates_template
coll_bl = db.blogs_blog

basic_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        XXsitemetasXX
        XXpagemetasXX
        XXsitelinksXX
        XXpagelinksXX
        XXsitestyleXX
        <title>XXtitleXX</title>
    </head>
    <body>
        XXsiteheaderXX
        XXcontentXX
        XXsitefooterXX
        XXsitescriptsXX
        XXpagescriptsXX
    </body>
    </html>"""

admin_doc = """<!DOCTYPE html>
    <html lang="en">
    <head>
        XXsitemetasXX
        XXpagemetasXX
        XXsitelinksXX
        XXpagelinksXX
        XXsitestyleXX
        <title>XXtitleXX</title>
    </head>
    <body>
        <!--##START siteheader START##-->
        XXsiteheaderXX
        <!--##END siteheader END##-->
        <!--##START content START##-->
        XXcontentXX
        <!--##END content END##-->
        <!--##START sitefooter START##-->
        XXsitefooterXX
        <!--##END sitefooter END##-->
        XXsitescriptsXX
        XXpagescriptsXX
        <div id="metas-and-style" style="display: none;">
            <textarea name="" id="pagemetas-form">XXpagemetasXX</textarea>
            <textarea name="" id="sitestyle-form">XXsitestyleXX</textarea>
        </div>
        <div id="hidden-form-attrs" style="display: none;">
            <textarea name="" id="siteid-form">XXsiteidXX</textarea>
            <textarea name="" id="pageroute-form">XXpagerouteXX</textarea>
        </div>
    </body>
    </html>"""


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f"""EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}""")

def replace_shortcodes(site, compiled):
    temp = list(coll_te.find({'id': site.id}, {'_id': 0}))[0]
    s = list(coll_si.find({'id': site.id}, {'_id': 0}))[0]
    for i in site.shortcodes:
        compiled = re.sub(f"XX{i.name}XX", f"{i.value}", compiled)
    for i in temp['shortcodes']:
        compiled = re.sub(f"XX{i['name']}XX", f"{i['value']}", compiled)
    for k, v in s.items():
        if type(v) is str:
            compiled = re.sub(f"XX{k}XX", f"{v}", compiled)
    html_sitemap = """<div><ul class="sitemap-links">"""
    for i in s['pages']:
        if re.search(r'(^/locations)|(^/registered-agents)|(^/telecom-agents)|(^/process-server)|(/blog/posts/id)|(/blog/posts)|(/html-sitemap)|(^/agents-by-state/)|(\.)', i['route']) is None:
                if i['route'] == "/":
                    html_sitemap += """<li><a href="/">Home</a></li>"""
                else:
                    html_sitemap += f"""<li><a href="{i['route']}">{i['title'] if i['title'] else " ".join(i['route'].split("/")).title()}</a></li>"""
    html_sitemap += """</ul></div>"""
    compiled = re.sub('XXsitemapXX', html_sitemap, compiled)
    compiled = re.sub(r'XX\w+XX', '', compiled)
    return compiled


def resource_page(request, site, pagedoc, **kwargs):
    mime_types = {
        '.css': 'text/css',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.jsonld': 'application/ld+json',
        '.php': 'application/x-httpd-php',
        '.ppp': 'application/x-httpd-php',
        '.pdf': 'application/pdf',
        '.jpeg': 'image/jpeg',
        '.ico': 'image/vnd.microsoft.icon',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
        '.sh': 'application/x-sh',
        '.xml': 'application/xml',
        '.zip': 'application/zip',
        '.7z': 'application/x-7z-compressed',
        '.gz': 'application/gzip',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    mime_type = "text/plain"
    for k, v in mime_types.items():
        regx = re.compile(f"{k}$")
        m = re.search(regx, kwargs['page'])
        if m is not None:
            mime_type = v
            break

    compiled = f"""{pagedoc.content}"""
    compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type=mime_type)

def static_page(request, site, pagedoc, dbg, admin, **kwargs):
    rep_codes = {
        'XXsitemetasXX': f"{site.sitemetas}",
        'XXpagemetasXX': f"{pagedoc.pagemetas}",
        'XXsitelinksXX': f"{site.sitelinks}",
        'XXpagelinksXX': f"{pagedoc.pagelinks}",
        'XXsitestyleXX': f"{site.sitestyle}",
        'XXtitleXX': f"{pagedoc.title}",
        'XXsiteheaderXX': f"{site.siteheader}",
        'XXcontentXX': f"{pagedoc.content}",
        'XXsitefooterXX': f"{site.sitefooter}",
        'XXsitescriptsXX': f"{site.sitescripts}",
        'XXpagescriptsXX': f"{pagedoc.pagescripts}",
        
    }
    compiled = f"{basic_doc}"
    if admin is True and dbg is True:
        compiled = f"{admin_doc}"
    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    if dbg is False:
        if pagedoc.route == "/agents-by-state":
            agents_by_state = """<div class="state-corps-links">"""
            for i in list(coll_ra.find({}, {'_id': 0}).distinct("state")):
                agents_by_state += f"""<a href="/agents-by-state/{i}/">{i}</a>"""
            agents_by_state += """</div>"""
            compiled = re.sub("XXagentsbystateXX", agents_by_state, compiled)
        compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type='text/html')

def individual_agent(request, site, pagename, dbg, admin, **kwargs):
    agent_obj = list(coll_ra.find({'id': kwargs['agentid'], 'agent': kwargs['agent']}, {'_id': 0}))
    if len(agent_obj):
        pagedoc = None
        for i in site.pages:
            if i.route == '/registered-agents/id':
                pagedoc = i
                break
        
        rep_codes = {
            'XXsitemetasXX': f"{site.sitemetas}",
            'XXpagemetasXX': f"{pagedoc.pagemetas}",
            'XXsitelinksXX': f"{site.sitelinks}",
            'XXpagelinksXX': f"{pagedoc.pagelinks}",
            'XXsitestyleXX': f"{site.sitestyle}",
            'XXtitleXX': f"{pagedoc.title}",
            'XXsiteheaderXX': f"{site.siteheader}",
            'XXcontentXX': f"{pagedoc.content}",
            'XXsitefooterXX': f"{site.sitefooter}",
            'XXsitescriptsXX': f"{site.sitescripts}",
            'XXpagescriptsXX': f"{pagedoc.pagescripts}",
            
        }
        compiled = f"{basic_doc}"

        for k, v in rep_codes.items():
            compiled = re.sub(k, v, compiled)

        for k, v in agent_obj[0].items():
            regx = re.compile(f"XX{k}XX")
            compiled = re.sub(regx, f"{v}", compiled)
        compiled = re.sub("XXrouteXX", f"{pagename}", compiled)
        compiled = replace_shortcodes(site, compiled)
        return HttpResponse(compiled, content_type='text/html')
    else:
        return HttpResponseNotFound()

def agents_by_location(request, site, pagename, dbg, admin, **kwargs):
    pagedoc = None
    route = "/agents-by-state"
    lwargs = dict()
    if len(kwargs) >= 1:
        lwargs['state'] = kwargs['arg_one']
        route = "/agents-by-state/state"
        if len(kwargs) == 2:
            lwargs['city'] = kwargs['arg_two']
            route = "/agents-by-state/state/city"

    for i in site.pages:
            if i.route == route:
                pagedoc = i
                break

    agents_objs = list(coll_ra.find(lwargs, {'_id': 0}))

    agent_table = """
    <div class="table-responsive">
        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
            <thead>
                <tr>
                    <th>Details</th>
                    <th>Registered Agent</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
    """
    for i in agents_objs:
        rel_link = urllib.parse.quote(f"/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        if dbg is True:
            rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        agent_table += f"""
                <tr>
                    <td><a href="{rel_link}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                    <td><a href="{rel_link}">{i['agent']}</a></td>
                    <td><a href="{rel_link}">{i['city']}, {i['state']}</a></td>
                </tr>
        """
    agent_table += """
            </tbody>
        </table>
    </div>
    """
    location_table = ""
    if len(lwargs) < 2:
        location_table = """<div class="process-server-corp-state-links">"""
        u_key = "state"
        if len(lwargs) == 1:
            u_key = "city"
        loc_objs = list(coll_ra.find(lwargs, {'_id': 0}).distinct(u_key))
        for i in loc_objs:
            rel_link = urllib.parse.quote(f"/agents-by-state/{'/'.join([*lwargs.values()])}/{i}/")
            if dbg is True:
                rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/agents-by-state/{'/'.join([*lwargs.values()])}/{i}/")
            location_table += f"""<a href="{rel_link}">{i}</a>"""
        location_table += "</div>"
    
    rep_codes = {
        'XXsitemetasXX': f"{site.sitemetas}",
        'XXpagemetasXX': f"{pagedoc.pagemetas}",
        'XXsitelinksXX': f"{site.sitelinks}",
        'XXpagelinksXX': f"{pagedoc.pagelinks}",
        'XXsitestyleXX': f"{site.sitestyle}",
        'XXtitleXX': f"{pagedoc.title}",
        'XXsiteheaderXX': f"{site.siteheader}",
        'XXcontentXX': f"{pagedoc.content}",
        'XXsitefooterXX': f"{site.sitefooter}",
        'XXsitescriptsXX': f"{site.sitescripts}",
        'XXpagescriptsXX': f"{pagedoc.pagescripts}",
        
    }
    compiled = f"{basic_doc}"

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    for k, v in lwargs.items():
        compiled = re.sub(f"XX{k}XX", v, compiled)
    compiled = re.sub("XXagentsXX", agent_table, compiled)
    compiled = re.sub("XXsublocationsXX", location_table, compiled)
    compiled = re.sub("XXrouteXX", f"{pagename}", compiled)
    compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type='text/html')

def agents_by_corp(request, site, pagename, dbg, admin, **kwargs):
    pagedoc = None
    route = ""
    lwargs = dict()
    if len(kwargs) >= 1:
        lwargs['agent'] = kwargs['arg_one']
        route = "/process-server/id"
        if len(kwargs) >= 2:
            lwargs['state'] = kwargs['arg_two']
            route = "/process-server/id/state"
            if len(kwargs) == 3:
                lwargs['city'] = kwargs['arg_three']
                route = "/process-server/id/state/city"

    for i in site.pages:
            if i.route == route:
                pagedoc = i
                break

    agents_objs = list(coll_ra.find(lwargs, {'_id': 0}))

    agent_table = """
    <div class="table-responsive">
        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
            <thead>
                <tr>
                    <th>Details</th>
                    <th>Registered Agent</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
    """
    for i in agents_objs:
        rel_link = urllib.parse.quote(f"/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        if dbg is True:
            rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        agent_table += f"""
                <tr>
                    <td><a href="{rel_link}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                    <td><a href="{rel_link}">{i['agent']}</a></td>
                    <td><a href="{rel_link}">{i['city']}, {i['state']}</a></td>
                </tr>
        """
    agent_table += """
            </tbody>
        </table>
    </div>
    """
    location_table = ""
    if len(lwargs) < 3:
        location_table = """<div class="process-server-corp-state-links">"""
        u_key = "agent"
        if len(lwargs) == 1:
            u_key = "state"
        elif len(lwargs) == 2:
            u_key = "city"
        res = list(coll_ra.find(lwargs, {'_id': 0}).distinct(u_key))
        for i in res:
            rel_link = urllib.parse.quote(f"/process-server/{'/'.join([*lwargs.values()])}/{i}/")
            if dbg is True:
                rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/process-server/{'/'.join([*lwargs.values()])}/{i}/")
            location_table += f"""<a href="{rel_link}">{i}</a>"""
        location_table += "</div>"

    rep_codes = {
        'XXsitemetasXX': f"{site.sitemetas}",
        'XXpagemetasXX': f"{pagedoc.pagemetas}",
        'XXsitelinksXX': f"{site.sitelinks}",
        'XXpagelinksXX': f"{pagedoc.pagelinks}",
        'XXsitestyleXX': f"{site.sitestyle}",
        'XXtitleXX': f"{pagedoc.title}",
        'XXsiteheaderXX': f"{site.siteheader}",
        'XXcontentXX': f"{pagedoc.content}",
        'XXsitefooterXX': f"{site.sitefooter}",
        'XXsitescriptsXX': f"{site.sitescripts}",
        'XXpagescriptsXX': f"{pagedoc.pagescripts}",
        
    }
    compiled = f"{basic_doc}"

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    for k, v in lwargs.items():
        compiled = re.sub(f"XX{k}XX", v, compiled)
    compiled = re.sub("XXagentsXX", agent_table, compiled)
    compiled = re.sub("XXsublocationsXX", location_table, compiled)
    compiled = re.sub("XXrouteXX", f"{pagename}", compiled)
    compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type='text/html')

def agents_query(request, site, pagename, dbg, admin, **kwargs):
    pagedoc = None
    route = '/registered-agents/search/key/value'

    for i in site.pages:
        if i.route == route:
            pagedoc = i
            break

    agents_objs = list(coll_ra.find({"$text":{"$search":kwargs['arg_two']}},{"score":{"$meta":"textScore"}}).sort([("score",{"$meta":"textScore"})]))

    agent_table = """
    <div class="table-responsive">
        <table id="default_order" class="table table-striped table-bordered display" style="width:100%">
            <thead>
                <tr>
                    <th>Details</th>
                    <th>Registered Agent</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody>
    """
    for i in agents_objs:
        rel_link = urllib.parse.quote(f"/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        if dbg is True:
            rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}/")
        agent_table += f"""
                <tr>
                    <td><a href="{rel_link}"><button type="button" class="btn waves-effect waves-light btn-info">Info</button></a></td>
                    <td><a href="{rel_link}">{i['agent']}</a></td>
                    <td><a href="{rel_link}">{i['city']}, {i['state']}</a></td>
                </tr>
        """
    agent_table += """
            </tbody>
        </table>
    </div>
    """

    rep_codes = {
        'XXsitemetasXX': f"{site.sitemetas}",
        'XXpagemetasXX': f"{pagedoc.pagemetas}",
        'XXsitelinksXX': f"{site.sitelinks}",
        'XXpagelinksXX': f"{pagedoc.pagelinks}",
        'XXsitestyleXX': f"{site.sitestyle}",
        'XXtitleXX': f"{pagedoc.title}",
        'XXsiteheaderXX': f"{site.siteheader}",
        'XXcontentXX': f"{pagedoc.content}",
        'XXsitefooterXX': f"{site.sitefooter}",
        'XXsitescriptsXX': f"{site.sitescripts}",
        'XXpagescriptsXX': f"{pagedoc.pagescripts}",
        
    }
    compiled = f"{basic_doc}"

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    compiled = re.sub("XXagentsXX", agent_table, compiled)
    compiled = re.sub("XXqueryXX", kwargs['arg_two'], compiled)
    compiled = re.sub("XXrouteXX", f"{pagename}", compiled)
    compiled = replace_shortcodes(site, compiled)
    return HttpResponse(compiled, content_type='text/html')

def sitemap_generator(request, site):
    states = list(coll_ra.find().distinct('state'))
    agents = list(coll_ra.find().distinct('agent'))
    pages = [i.route for i in site.pages if re.search(re.compile("^/((registered-agents)|(process-server)|(agents-by-state)|([\w-]+\.\w{2,4}))"), f"{i.route}") is None]
    process_server_urls = []
    registered_agent_urls = []
    agents_by_state_urls = []
    page_urls = []
    xml_urls = []
    #print(agents)

    for i in agents:
        process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/process-server/{i}""")+"</loc>\n\t</url>")
        a_states = list(coll_ra.find({"agent": i}).distinct("state"))
        #print(a_states)
        for n in a_states:
            process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/process-server/{i}/{n}""")+"</loc>\n\t</url>")
            a_cities = list(coll_ra.find({"agent": i, 'state': n}).distinct("city"))
            #print(a_cities)
            for k in a_cities:
                process_server_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/process-server/{i}/{n}/{k}""")+"</loc>\n\t</url>")
    process_server_urls.sort()
    process_server_urls.sort(key=len, reverse=True)

    for n in states:
        agents_by_state_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/agents-by-state/{n}""")+"</loc>\n\t</url>")
        s_cities = list(coll_ra.find({'state': n}).distinct("city"))
        #print(s_cities)
        for k in s_cities:
            agents_by_state_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/agents-by-state/{n}/{k}""")+"</loc>\n\t</url>")
    agents_by_state_urls.sort()
    agents_by_state_urls.sort(key=len, reverse=True)

    for i in list(coll_ra.find({}, {'_id': 0})):
        registered_agent_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""/registered-agents/{i['agent']}/{i['state']}/{i['county']}/{i['city']}/{i['id']}""")+"</loc>\n\t</url>")
    registered_agent_urls.sort()
    registered_agent_urls.sort(key=len, reverse=True)

    for i in pages:
        page_urls.append(f'\n\t<url>\n\t\t<loc>https://www.{site.sitename}.com'+urllib.parse.quote(f"""{i}""")+"</loc>\n\t</url>")

    print(len(page_urls))
    print(len(registered_agent_urls))
    print(len(process_server_urls))
    print(len(agents_by_state_urls))
    print(len(page_urls)+len(registered_agent_urls)+len(process_server_urls)+len(agents_by_state_urls))
    xml_urls = ''.join(page_urls) + ''.join(registered_agent_urls) + ''.join(process_server_urls) + ''.join(agents_by_state_urls)
    
    xml_doc = """<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""" + xml_urls + """\n</urlset>"""
    return HttpResponse(xml_doc, content_type="application/xml")


