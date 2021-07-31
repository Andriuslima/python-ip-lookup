import asyncio
import sys
import mmap
import re
from requests.exceptions import Timeout
from requests_cache import CachedSession
from datetime import timedelta
import untangle
import json

INPUT_FILE = sys.argv[1]
OUTPUT_FILE = 'output.json'
GEO_REQUEST_TIMEOUT = 2
RDAP_REQUEST_TIMEOUT = 2
IP_PATTERN = re.compile(rb'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
RDAP_URL = 'https://rdap-bootstrap.arin.net/bootstrap/ip/%s'
GEP_IP_URL = 'http://api.geoiplookup.net/?query=%s'

session = CachedSession(expire_after=timedelta(days=1))


def search_ips(name) -> str:
    """
    Function that opens the file with `name` and yields each unique IP found.
    An IP will never be yield more than once.

    Returns
    -------
    str: ip found
    """
    found = []
    with open(name, 'r+b') as file:
        memory_file = mmap.mmap(file.fileno(), length=0,
                                access=mmap.ACCESS_READ)
        for line in iter(memory_file.readline, b""):
            for match in re.finditer(IP_PATTERN, line):
                ip_match = match.group().strip().decode("utf-8")
                if ip_match not in found:
                    found.append(ip_match)
                    yield ip_match
        print('%s unique ips found' % len(found))


def write_output(data) -> bool:
    with open(OUTPUT_FILE, 'w') as output:
        output.write(json.dumps(data))
    return True


def rdap_ip(ip_rdap_lookup) -> dict:
    """
    Function that performs RDAP lookup given the ip `ip_rdap_lookup`

    Returns
    -------
    dict: Information about RDAP
    """
    try:
        response = session.get(RDAP_URL % ip_rdap_lookup,
                               timeout=RDAP_REQUEST_TIMEOUT)
        if response.status_code >= 300:
            return {'error': 'Information Not Found'}
        return json.loads(response.text)
    except Timeout:
        return {'error': 'Timeout received'}


def geo_ip(ip_geo_lookup) -> dict:
    """
    Function that performs GeoIP lookup given the ip `ip_geo_lookup`

    Returns
    -------
    dict: Information about GeoIP
    """
    try:
        response = session.get(GEP_IP_URL %
                               ip_geo_lookup, timeout=GEO_REQUEST_TIMEOUT)
        if response.status_code >= 300:
            return {'error': 'Information Not Found'}
        xml = untangle.parse(response.text).ip.results.result
        return {'host': xml.host.cdata, 'country': xml.countryname.cdata, 'city': xml.city.cdata}
    except Timeout:
        return {'error': 'Timeout received'}


async def get_ip_info(search_ip) -> dict:
    """
    Function that gathers GeoIP and RDAP lookup given the ip `search_ip`

    Returns
    -------
    dict: Information about GeoIP and RDAP
    """
    geo = geo_ip(search_ip)
    rdap = rdap_ip(search_ip)
    return {search_ip: {'geoIp': geo, 'rdap': rdap}}


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    tasks = [get_ip_info(ip) for ip in search_ips(INPUT_FILE)]
    ips = loop.run_until_complete(asyncio.gather(*tasks))
    done = write_output(ips)
    if done:
        print('Output written: %s' % OUTPUT_FILE)
