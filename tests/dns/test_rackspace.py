# -*- coding:utf-8 -*-
from __future__ import with_statement
import sys
import unittest2
import httplib

try:
    import simplejson as json
except ImportError:
    import json

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse
import libcloud
from libcloud.dns.types import RecordType
from test.dns.test_rackspace import RackspaceMockHttp, RackspaceUSDNSDriver
from libcloud.dns.base import Zone
from mock import patch

from libcloud_rest.api.versions import versions as rest_versions
from libcloud_rest.application import LibcloudRestApp
from libcloud_rest.exception import NoSuchZoneError, LibcloudError, \
    NoSuchRecordError, ValidationError
from tests.file_fixtures import DNSFixtures


class RackspaceUSTests(unittest2.TestCase):
    def setUp(self):
        self.url_tmpl = rest_versions[libcloud.__version__] +\
                        '/dns/RACKSPACE_US/%s?test=1'
        self.client = Client(LibcloudRestApp(), BaseResponse)
        self.fixtures = DNSFixtures('rackspace_us')
        self.headers = {'x-auth-user': 'user', 'x-api-key': 'key'}
        RackspaceMockHttp.type = None

    def test_list_zones(self):
        url = self.url_tmpl % ('zones')
        resp = self.client.get(url, headers=self.headers)
        zones = json.loads(resp.data)
        self.assertEqual(len(zones), 6)
        self.assertEqual(zones[0]['domain'], 'foo4.bar.com')
        self.assertEqual(resp.status_code, httplib.OK)

    def test_list_zones_not_successful(self):
        RackspaceMockHttp.type = '413'
        url = self.url_tmpl % ('zones')
        resp = self.client.get(url, headers=self.headers)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.INTERNAL_SERVER_ERROR)
        self.assertEqual(resp_data['error']['code'], LibcloudError.code)

    def test_list_zones_no_result(self):
        RackspaceMockHttp.type = 'NO_RESULTS'
        url = self.url_tmpl % ('zones')
        resp = self.client.get(url, headers=self.headers)
        zones = json.loads(resp.data)
        self.assertEqual(len(zones), 0)
        self.assertEqual(resp.status_code, httplib.OK)

    def test_list_records_success(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zones_resp_data = json.loads(zones_resp.data)
        zone_id = zones_resp_data[0]['id']
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id), 'records']))
        resp = self.client.get(url, headers=self.headers)
        records = json.loads(resp.data)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]['name'], 'test3')
        self.assertEqual(records[0]['type'], RecordType.A)
        self.assertEqual(records[0]['data'], '127.7.7.7')
        self.assertEqual(resp.status_code, httplib.OK)

    def test_list_records_zone_does_not_exist(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zones_resp_data = json.loads(zones_resp.data)
        zone_id = zones_resp_data[0]['id']
        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id), 'records']))
        resp = self.client.get(url, headers=self.headers)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp_data['error']['code'], NoSuchZoneError.code)

    def test_update_zone_not_successful(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zones_resp_data = json.loads(zones_resp.data)
        zone_id = zones_resp_data[0]['id']
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id)]))
        resp = self.client.put(url, headers=self.headers,
                               data='{"domain": "libcloud.org"}',
                               content_type='application/json')
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.INTERNAL_SERVER_ERROR)
        self.assertEqual(resp_data['error']['code'], LibcloudError.code)

    def test_delete_zone_success(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zones_resp_data = json.loads(zones_resp.data)
        zone_id = zones_resp_data[0]['id']
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id)]))
        resp = self.client.delete(url, headers=self.headers)
        self.assertEqual(resp.status_code, 204)

    def test_delete_does_not_exists(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zones_resp_data = json.loads(zones_resp.data)
        zone_id = zones_resp_data[0]['id']
        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id)]))
        resp = self.client.delete(url, headers=self.headers)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp_data['error']['code'], NoSuchZoneError.code)

    def test_get_record_success(self):
        RackspaceMockHttp.type = None
        zone_id = '12345678'
        record_id = '23456789'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id),
                                         'records', str(record_id)]))
        resp = self.client.get(url, headers=self.headers)
        record = json.loads(resp.data)
        self.assertEqual(record['id'], 'A-7423034')
        self.assertEqual(record['name'], 'test3')
        self.assertEqual(record['type'], RecordType.A)
        self.assertEqual(resp.status_code, httplib.OK)

    def test_get_record_zone_does_not_exist(self):
        RackspaceMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        zone_id = '444'
        record_id = '23456789'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id),
                                         'records', str(record_id)]))
        resp = self.client.get(url, headers=self.headers)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp_data['error']['code'], NoSuchZoneError.code)

    def test_get_record_record_does_not_exist(self):
        RackspaceMockHttp.type = 'RECORD_DOES_NOT_EXIST'
        zone_id = '12345678'
        record_id = '28536'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id),
                                         'records', str(record_id)]))
        resp = self.client.get(url, headers=self.headers)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.NOT_FOUND)
        self.assertEqual(resp_data['error']['code'], NoSuchRecordError.code)

    def test_create_record_success(self):
        url = self.url_tmpl % ('zones')
        zones_resp = self.client.get(url, headers=self.headers)
        zone_data = json.loads(zones_resp.data)[0]
        zone_id = zone_data['id']
        zone = Zone(zone_id, zone_data['domain'], zone_data['type'],
                    zone_data['ttl'], None)

        RackspaceMockHttp.type = 'CREATE_RECORD'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id), 'records']))
        test_request = self.fixtures.load('create_record.json')
        test_request_json = json.loads(test_request)
        with patch.object(RackspaceUSDNSDriver, 'get_zone',
                          mocksignature=True) as get_zone_mock:
            get_zone_mock.return_value = zone
            resp = self.client.post(url, headers=self.headers,
                                    data=json.dumps(test_request_json),
                                    content_type='application/json')
        record = json.loads(resp.data)
        self.assertEqual(record['id'], 'A-7423317')
        self.assertEqual(record['name'], 'www')
        self.assertEqual(record['type'], RecordType.A)
        self.assertEqual(record['data'], '127.1.1.1')
        self.assertEqual(resp.status_code, httplib.CREATED)

    def test_create_record_validation_error(self):
        zone_id = '123'
        url = self.url_tmpl % ('/'.join(['zones', str(zone_id), 'records']))
        test_request = self.fixtures.load('create_record_invalid.json')
        test_request_json = json.loads(test_request)
        resp = self.client.post(url, headers=self.headers,
                                data=json.dumps(test_request_json),
                                content_type='application/json')
        resp_data = json.loads(resp.data)
        self.assertEqual(resp.status_code, httplib.BAD_REQUEST)
        self.assertEqual(resp_data['error']['code'], ValidationError.code)


if __name__ == '__main__':
    import tests
    sys.exit(unittest2.main())
