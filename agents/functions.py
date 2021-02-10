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


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f"""EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}""")


def resource_page(request, site, pagedoc, **kwargs):
    mime_types = {
        '.css': 'text/css',
        '.csv': 'text/csv',
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.jsonld': 'application/ld+json',
        '.php': 'application/x-httpd-php',
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
    return HttpResponse(compiled, content_type=mime_type)

def static_page(request, site, pagedoc, **kwargs):
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
    compiled = f"""<!DOCTYPE html>
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

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)
    return HttpResponse(compiled, content_type='text/html')

def individual_agent(request, site, pagename, **kwargs):
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
        compiled = f"""<!DOCTYPE html>
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
            <!-- XXagentXX -->
            <!-- XXstateXX -->
            <!-- XXstateacronymXX -->
            <!-- XXcountyXX -->
            <!-- XXcityXX -->
            <!-- XXzipXX -->
            <!-- XXaddressXX -->
            <!-- XXupdatedXX -->
            <!-- XXcreatedXX -->
            XXsiteheaderXX
            XXcontentXX
            XXsitefooterXX
            XXsitescriptsXX
            XXpagescriptsXX
        </body>
        </html>"""

        for k, v in rep_codes.items():
            compiled = re.sub(k, v, compiled)

        for k, v in agent_obj[0].items():
            regx = re.compile(f"XX{k}XX")
            compiled = re.sub(regx, f"{v}", compiled)
        return HttpResponse(compiled, content_type='text/html')
    else:
        return HttpResponseNotFound()

def agents_by_location(request, site, pagename, **kwargs):
    dbg = True
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
        rel_link = urllib.parse.quote(f"/registered-agents/{i['agent']}/{i['id']}/")
        if dbg is True:
            rel_link = urllib.parse.quote(f"/agents/compile/{site.id}/registered-agents/{i['agent']}/{i['id']}/")
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
    compiled = f"""<!DOCTYPE html>
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
        XXsublocationsXX
        XXsitefooterXX
        XXsitescriptsXX
        XXpagescriptsXX
    </body>
    </html>"""

    for k, v in rep_codes.items():
        compiled = re.sub(k, v, compiled)

    compiled = re.sub("XXagentsXX", agent_table, compiled)

    compiled = re.sub("XXsublocationsXX", location_table, compiled)

    return HttpResponse(compiled, content_type='text/html')

def agents_by_corp(request, site, pagename, **kwargs):
    compiled = "agents by corp"
    return HttpResponse(compiled, content_type='text/plain')

def agents_query(request, site, pagename, **kwargs):
    compiled = "agents query"
    return HttpResponse(compiled, content_type='text/plain')

def sitemap_generator(request, **kwargs):
    return "sitemap generator"


