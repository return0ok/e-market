from rest_framework.versioning import BaseVersioning

class HeaderVersioning(BaseVersioning):
    version_param = 'version'
    default_version = '1.0'
    print("TESTtttttttttttttttttttt")

    def determine_version(self, request, *args, **kwargs):
        header_version = request.headers.get('X-API-Version')
        print(header_version)
        if header_version:
            return header_version

        accept_header = request.headers.get('Accept')
        if accept_header and 'version=' in accept_header:
            accept_version = accept_header.split('version=')[1].split(';')[0]
            return accept_version
            print(header_version)
        return self.default_version
        print(header_version)