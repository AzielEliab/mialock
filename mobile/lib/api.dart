import 'dart:convert';

import 'package:http/http.dart' as http;

/// Hosted M.I.A.Lock Worker. Always send User-Agent Mozilla/5.0.
const kHost = 'https://mialock-download-tracker.vibelock.workers.dev';
const kUserAgent = 'Mozilla/5.0';

const kLimitation =
    'M.I.A.Lock shows documented events for one person: '
    'date × time × event × duration. Doe results are compatibility leads '
    'to check with the source record. Coverage color shows how thoroughly '
    'a source was searched. Author Aziel Eliab.';

const kMotto =
    'Search broadly. Match probabilistically. Challenge every hit. '
    'Preserve provenance. Verify before action.';

const kDoeHonesty =
    'Doe hits are compatibility leads only — never an identification. '
    'Rank scores are uncalibrated operational labels, not the probability '
    'that a notice is the missing person. Doe hit ≠ ID.';

const kCoverageHonesty =
    'Coverage heat is search intensity / negative-evidence weight — '
    'not a probability of presence.';

/// Elena Vargas hosted demo descriptor (same payload as Worker /v1/example).
const kDemoDescriptor = <String, Object>{
  'mode': 'doe_cold',
  'name': 'Elena Vargas',
  'aliases': 'Elena Vargas',
  'jurisdiction': 'US-IL-COOK',
  'year_from': '1994',
  'year_to': '1995',
  'age_band': '20-30',
  'sex': 'female',
  'height_cm': 165,
  'build': 'slim',
  'scars_marks': 'tattoo left wrist',
  'clothing': 'red jacket',
  'time_window_from': '1994-09-02',
  'time_window_to': '1995-12-31',
};

class MiaLockApi {
  MiaLockApi({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  static const _timeout = Duration(seconds: 20);

  Future<Map<String, dynamic>> health() => _get('/v1/health');

  Future<Map<String, dynamic>> map() => _get('/v1/map');

  Future<Map<String, dynamic>> searchOptions() => _get('/v1/search-options');

  Future<Map<String, dynamic>> queries(Map<String, Object?> body) =>
      _post('/v1/queries', body);

  Future<Map<String, dynamic>> doeMatch(Map<String, Object?> body) =>
      _post('/v1/doe-match', body);

  Future<Map<String, dynamic>> coverage({String subject = 'subj-elena-cold-demo'}) =>
      _get('/v1/coverage?subject=${Uri.encodeQueryComponent(subject)}');

  Future<Map<String, dynamic>> _get(String path) async {
    final res = await _client
        .get(
          Uri.parse('$kHost$path'),
          headers: {
            'User-Agent': kUserAgent,
            'Accept': 'application/json',
          },
        )
        .timeout(_timeout);
    return _decode(path, res);
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, Object?> body,
  ) async {
    final res = await _client
        .post(
          Uri.parse('$kHost$path'),
          headers: {
            'User-Agent': kUserAgent,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(body),
        )
        .timeout(_timeout);
    return _decode(path, res);
  }

  Map<String, dynamic> _decode(String path, http.Response res) {
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw Exception('HTTP ${res.statusCode} on $path');
    }
    final decoded = jsonDecode(res.body);
    if (decoded is Map<String, dynamic>) return decoded;
    if (decoded is Map) return Map<String, dynamic>.from(decoded);
    throw Exception('Unexpected JSON on $path');
  }
}
