# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import JsonResponse
from api.models import DetectResult, Category, Manager, Application
from datetime import datetime
from api.helpers import *
import json

'''
/api/detections
Supported HTTP types -> [POST, PUT]

This api is used for NLP service to submit new detection results to 
backend systems or updated results for existed entries.
POST to create new entries.
PUT to update existing entries.

Request JSON format:
    app_name:       string          name of the app
    manager_name:   string          name of the manager
    corp_sector:    string          corporation sector it belongs to
    business:       string          business department it belongs to
    result:         dict of records detection results

    where a typical `result` looks like this:
    {
        "col47":    [1.0, 2.5, 3.6],
        "nameCol":  [5.9, 6.0, 3.0]
    }

Return:
    A JSON which contains execution information.
    If it succeeds, following JSON will return:
    {
        "status": "ok"
    }
    Or an error JSON will return:
    {
        "status": "error",
        "reason": "reason of failure"
    }

'''
def rest_detection(request):

    if request.method not in ['POST', 'PUT']:
        return JsonResponse(error_response('Only supports PUT/POST.'), 
                            status=403)
    # Only supports POST and PUT

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        print e
        print request.body
        return JsonResponse(error_response('Invalid JSON format.'), 
                            status=403)
    # Parse JSON data
    
    app_name = regularize_str(data.get('app_name'))
    manager_name = regularize_str(data.get('manager_name'))
    corp_sector = regularize_str(data.get('corp_sector'))
    business = regularize_str(data.get('business'))
    # Get regularized strings and identifier

    last_updated = datetime.now()
    result = data.get('result', dict())
    # Get detected and result


    if len(result) == 0:
        return JsonResponse(error_response('No detection results in JSON.'), 
                            status=403)
    
    vec_len = len(result[result.keys()[0]])
    for col in result.keys():
        if len(result[col]) != vec_len:
            return JsonResponse(error_response('Lengths of vectors aren\'t the same'), 
                            status=403)
    
    if request.method == 'POST':

        items = DetectResult.objects(app_name=app_name, manager_name=manager_name,
                                     corp_sector=corp_sector, business=business)
        if items.count() != 0:
            return JsonResponse(
                error_response('Record already exists. You should use PUT.'))
        # If identifier already exists -> invalid POST

        res = DetectResult()
        res.app_name = app_name
        res.manager_name = manager_name
        res.corp_sector = corp_sector
        res.business = business
        res.result = result 
        res.last_updated = last_updated
        # New instance
        
        try:
            res.save()
        except Exception as e:
            print e
            return JsonResponse(error_response('Wrong format of some items in JSON.'), 
                                status=403)
        # Save

    elif request.method == 'PUT':
        items = DetectResult.objects(app_name=app_name, manager_name=manager_name,
                                     corp_sector=corp_sector, business=business)
        if items.count() == 0:
            return JsonResponse(
                error_response('Record doesn\'t exists You should use POST.'))
        # Record should exist in the database
        
        res = items.first()
        res.result = result
        res.last_updated = last_updated
        # Update detected and result

        try:
            res.save()
        except Exception as e:
            print e
            return JsonResponse(error_response('Wrong format of some items in JSON.'), 
                                status=403)
        # Save
    
    cate = Category.objects(corp_sector=corp_sector).first()
    if not cate:
        new_cate = Category()
        new_cate.corp_sector = corp_sector
        new_cate.business = [business]
        new_cate.save()
    elif business not in cate.business:
        cate.business.append(business)
        cate.save()
    # Update category information
    
    manager = Manager.objects(manager_name=manager_name).first()
    if not manager:
        new_manager = Manager()
        new_manager.manager_name = manager_name
        new_manager.save()
    
    app = Application.objects(name=app_name).first()
    if not app:
        app = Application()
        app.name = app_name
        app.save()

    return JsonResponse(ok_response(), status=200)
    # Success
