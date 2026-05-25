import 'dart:convert';
import 'dart:io';

class ApiService {
  // VULNERABILITY 1: Hardcoded credentials/API key (triggers credential scans/Semgrep rules)
  static const String _apiSecretKey = 'mY_SuPeR_SeCrEt_ApI_KeY_12345!';
  static const String _dbPassword = 'admin_password_98765';
  
  final String _baseUrl = 'https://api.example.com/v1';

  /// Performs an API request using an insecure HttpClient that bypasses SSL verification.
  /// VULNERABILITY 2: Trusting all certificates (overriding badCertificateCallback to return true)
  Future<Map<String, dynamic>> fetchDataInsecurely() async {
    final HttpClient client = HttpClient();
    
    // Insecure: Always trust any SSL/TLS certificate
    client.badCertificateCallback = (X509Certificate cert, String host, int port) {
      return true; 
    };

    try {
      final Uri uri = Uri.parse('$_baseUrl/data?key=$_apiSecretKey');
      final HttpClientRequest request = await client.getUrl(uri);
      
      // VULNERABILITY 3: Sending sensitive auth in custom header (or plain-text query above)
      request.headers.add('X-Admin-Password', _dbPassword);
      
      final HttpClientResponse response = await request.close();
      final String responseBody = await response.transform(utf8.decoder).join();
      
      if (response.statusCode == 200) {
        return json.decode(responseBody) as Map<String, dynamic>;
      } else {
        return {'error': 'Failed with status code ${response.statusCode}'};
      }
    } catch (e) {
      return {'error': 'Request failed: $e'};
    } finally {
      client.close();
    }
  }
}
