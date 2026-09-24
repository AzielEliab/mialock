import 'package:flutter/material.dart';

import 'api.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MiaLockApp());
}

class MiaLockApp extends StatelessWidget {
  const MiaLockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'M.I.A.Lock',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(Brightness.light),
      darkTheme: buildAppTheme(Brightness.dark),
      themeMode: ThemeMode.system,
      home: const ShellPage(),
    );
  }
}

class ShellPage extends StatefulWidget {
  const ShellPage({super.key});

  @override
  State<ShellPage> createState() => _ShellPageState();
}

class _ShellPageState extends State<ShellPage> {
  final api = MiaLockApi();
  int index = 0;
  late final pages = [
    MapPage(api: api),
    SearchPage(api: api),
    DoePage(api: api),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                'assets/sigil.png',
                width: 32,
                height: 32,
                semanticLabel: '',
              ),
            ),
            const SizedBox(width: 10),
            const Flexible(
              child: Text('M.I.A.Lock'),
            ),
          ],
        ),
      ),
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.map_outlined), label: 'Map'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.badge_outlined), label: 'Doe leads'),
        ],
      ),
    );
  }
}

class HonestyBanner extends StatelessWidget {
  const HonestyBanner({super.key, required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0x33241C0D),
        border: Border.all(color: const Color(0x885C4A1A)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: kWarn),
      ),
    );
  }
}

class ErrorCard extends StatelessWidget {
  const ErrorCard({super.key, required this.error, required this.onRetry});
  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Could not reach the Worker.', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('$error'),
            const SizedBox(height: 12),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

class MapPage extends StatefulWidget {
  const MapPage({super.key, required this.api});
  final MiaLockApi api;

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  late Future<Map<String, dynamic>> future;
  Map<String, dynamic>? coverage;
  String? coverageSubject;
  Object? coverageError;
  bool coverageLoading = false;

  @override
  void initState() {
    super.initState();
    future = widget.api.map();
  }

  void _reload() => setState(() => future = widget.api.map());

  Widget _personTile(Object raw) {
    final person = Map<String, dynamic>.from(raw as Map);
    return _PersonCard(
      person: person,
      onCoverage: () => _loadCoverage('${person['subject_id']}'),
    );
  }

  Future<void> _loadCoverage(String subject) async {
    setState(() {
      coverageLoading = true;
      coverageError = null;
      coverageSubject = subject;
    });
    try {
      final payload = await widget.api.coverage(subject: subject);
      if (!mounted) return;
      setState(() {
        coverage = payload;
        coverageLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        coverageError = e;
        coverageLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: future,
      builder: (context, snap) {
        if (snap.hasError) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [ErrorCard(error: snap.error!, onRetry: _reload)],
          );
        }
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final data = snap.data!;
        final people = (data['people'] as List?) ?? const [];
        final layers = (data['layers'] as Map?) ?? const {};
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Documented events for each person — date, time, place, and duration.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              data['note']?.toString() ??
                  'This phone view reads the sample casebook. The full map is mialock ui on your computer.',
            ),
            const SizedBox(height: 16),
            Text('Sample casebook', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            for (final raw in people)
              _personTile(raw),
            if (coverageLoading) ...[
              const SizedBox(height: 12),
              const Center(child: CircularProgressIndicator()),
            ],
            if (coverageError != null) ...[
              const SizedBox(height: 12),
              ErrorCard(error: coverageError!, onRetry: () {
                final s = coverageSubject;
                if (s != null) _loadCoverage(s);
              }),
            ],
            if (coverage != null) ...[
              const SizedBox(height: 12),
              _CoverageCard(payload: coverage!),
            ],
            const SizedBox(height: 16),
            ExpansionTile(
              title: const Text('About'),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(kLimitation),
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Uncertainty ellipses: ${layers['uncertainty_ellipses'] ?? 'drawn from the location recorded with the event.'}',
                  ),
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(kCoverageHonesty),
                ),
                const SizedBox(height: 8),
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text('Author Aziel Eliab. The full map on a computer is mialock ui.'),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _PersonCard extends StatelessWidget {
  const _PersonCard({required this.person, required this.onCoverage});
  final Map<String, dynamic> person;
  final VoidCallback onCoverage;

  @override
  Widget build(BuildContext context) {
    final span = (person['span'] as Map?) ?? const {};
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${person['display_name'] ?? person['subject_id']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text('${person['summary'] ?? ''}'),
            const SizedBox(height: 8),
            Text(
              '${person['case_kind']} · ${person['pin_count']} pins · '
              '${span['start'] ?? '—'} → ${span['end'] ?? '—'}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: kGold),
            ),
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: const Text('Advanced'),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.tonal(
                    onPressed: onCoverage,
                    child: const Text('Show search coverage'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CoverageCard extends StatelessWidget {
  const _CoverageCard({required this.payload});
  final Map<String, dynamic> payload;

  @override
  Widget build(BuildContext context) {
    final adapters = (payload['adapters_run'] as List?) ?? const [];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Coverage for ${payload['subject_id'] ?? payload['case_id']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 6),
            HonestyBanner(text: '${payload['framing'] ?? kCoverageHonesty}'),
            const SizedBox(height: 8),
            Text('${payload['note'] ?? ''}'),
            const SizedBox(height: 8),
            for (final raw in adapters)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  '${(raw as Map)['source_id']} · ${(raw)['jurisdiction']} · '
                  'est ${(raw)['coverage_estimate']} · ${(raw)['result']}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class SearchPage extends StatefulWidget {
  const SearchPage({super.key, required this.api});
  final MiaLockApi api;

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  late Future<Map<String, dynamic>> modesFuture;
  final name = TextEditingController(text: '${kDemoDescriptor['name']}');
  final jurisdiction = TextEditingController(text: '${kDemoDescriptor['jurisdiction']}');
  final ageBand = TextEditingController(text: '${kDemoDescriptor['age_band']}');
  final sex = TextEditingController(text: '${kDemoDescriptor['sex']}');
  String mode = 'doe_cold';
  Map<String, dynamic>? queries;
  Object? queryError;
  bool queryLoading = false;

  @override
  void initState() {
    super.initState();
    modesFuture = widget.api.searchOptions();
  }

  @override
  void dispose() {
    name.dispose();
    jurisdiction.dispose();
    ageBand.dispose();
    sex.dispose();
    super.dispose();
  }

  void _reloadModes() => setState(() => modesFuture = widget.api.searchOptions());

  Future<void> _render() async {
    setState(() {
      queryLoading = true;
      queryError = null;
    });
    try {
      final payload = await widget.api.queries({
        'mode': mode,
        'name': name.text.trim(),
        'aliases': name.text.trim(),
        'jurisdiction': jurisdiction.text.trim(),
        'age_band': ageBand.text.trim(),
        'sex': sex.text.trim(),
      });
      if (!mounted) return;
      setState(() {
        queries = payload;
        queryLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        queryError = e;
        queryLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: modesFuture,
      builder: (context, snap) {
        if (snap.hasError) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [ErrorCard(error: snap.error!, onRetry: _reloadModes)],
          );
        }
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final modes = ((snap.data!['modes'] as List?) ?? const [])
            .map((m) => Map<String, dynamic>.from(m as Map))
            .toList();
        if (modes.isNotEmpty && !modes.any((m) => m['mode_id'] == mode)) {
          mode = '${modes.first['mode_id']}';
        }
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Write search text for a mode.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: mode,
              decoration: const InputDecoration(
                labelText: 'Search mode',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final m in modes)
                  DropdownMenuItem(
                    value: '${m['mode_id']}',
                    child: Text('${m['title'] ?? m['mode_id']}'),
                  ),
              ],
              onChanged: (v) {
                if (v != null) setState(() => mode = v);
              },
            ),
            const SizedBox(height: 12),
            if (modes.isNotEmpty)
              Text(
                '${modes.firstWhere((m) => m['mode_id'] == mode, orElse: () => modes.first)['summary'] ?? ''}',
              ),
            const SizedBox(height: 12),
            TextField(
              controller: name,
              decoration: const InputDecoration(
                labelText: 'Name / aliases',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: jurisdiction,
              decoration: const InputDecoration(
                labelText: 'Jurisdiction',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: ageBand,
              decoration: const InputDecoration(
                labelText: 'Age band',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: sex,
              decoration: const InputDecoration(
                labelText: 'Sex (descriptor, not an ID)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: queryLoading ? null : _render,
              child: const Text('Render search plans'),
            ),
            if (queryLoading) ...[
              const SizedBox(height: 12),
              const Center(child: CircularProgressIndicator()),
            ],
            if (queryError != null) ...[
              const SizedBox(height: 12),
              ErrorCard(error: queryError!, onRetry: _render),
            ],
            if (queries != null) ...[
              const SizedBox(height: 16),
              Text('${queries!['title'] ?? mode}', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              const Text('These are search plans to run yourself.'),
              const SizedBox(height: 8),
              for (final raw in (queries!['queries'] as List? ?? const []))
                _QueryCard(query: Map<String, dynamic>.from(raw as Map)),
            ],
          ],
        );
      },
    );
  }
}

class _QueryCard extends StatelessWidget {
  const _QueryCard({required this.query});
  final Map<String, dynamic> query;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${query['title'] ?? query['family_id']}', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 6),
            SelectableText(
              '${query['rendered'] ?? query['template']}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontFamily: 'monospace',
                    color: kGold,
                  ),
            ),
            if ('${query['notes'] ?? ''}'.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text('${query['notes']}'),
            ],
          ],
        ),
      ),
    );
  }
}

class DoePage extends StatefulWidget {
  const DoePage({super.key, required this.api});
  final MiaLockApi api;

  @override
  State<DoePage> createState() => _DoePageState();
}

class _DoePageState extends State<DoePage> {
  final ageBand = TextEditingController(text: '${kDemoDescriptor['age_band']}');
  final sex = TextEditingController(text: '${kDemoDescriptor['sex']}');
  final height = TextEditingController(text: '${kDemoDescriptor['height_cm']}');
  final build = TextEditingController(text: '${kDemoDescriptor['build']}');
  final marks = TextEditingController(text: '${kDemoDescriptor['scars_marks']}');
  final clothing = TextEditingController(text: '${kDemoDescriptor['clothing']}');
  final jurisdiction = TextEditingController(text: '${kDemoDescriptor['jurisdiction']}');
  final timeFrom = TextEditingController(text: '${kDemoDescriptor['time_window_from']}');
  final timeTo = TextEditingController(text: '${kDemoDescriptor['time_window_to']}');
  Map<String, dynamic>? result;
  Object? error;
  bool loading = false;

  @override
  void dispose() {
    ageBand.dispose();
    sex.dispose();
    height.dispose();
    build.dispose();
    marks.dispose();
    clothing.dispose();
    jurisdiction.dispose();
    timeFrom.dispose();
    timeTo.dispose();
    super.dispose();
  }

  Future<void> _rank() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      final payload = await widget.api.doeMatch({
        'age_band': ageBand.text.trim(),
        'sex': sex.text.trim(),
        'height_cm': num.tryParse(height.text.trim()) ?? height.text.trim(),
        'build': build.text.trim(),
        'scars_marks': marks.text.trim(),
        'clothing': clothing.text.trim(),
        'jurisdiction': jurisdiction.text.trim(),
        'time_window_from': timeFrom.text.trim(),
        'time_window_to': timeTo.text.trim(),
      });
      if (!mounted) return;
      setState(() {
        result = payload;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = e;
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Compare a description with public Doe notices.',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        const Text('A result is a lead to check with the source record.'),
        const SizedBox(height: 12),
        _field(ageBand, 'Age band'),
        _field(sex, 'Sex'),
        _field(height, 'Height (cm)'),
        _field(build, 'Build'),
        _field(marks, 'Scars / marks'),
        _field(clothing, 'Clothing'),
        _field(jurisdiction, 'Jurisdiction'),
        _field(timeFrom, 'Time window from'),
        _field(timeTo, 'Time window to'),
        FilledButton(
          onPressed: loading ? null : _rank,
          child: const Text('Rank compatibility leads'),
        ),
        if (loading) ...[
          const SizedBox(height: 12),
          const Center(child: CircularProgressIndicator()),
        ],
        if (error != null) ...[
          const SizedBox(height: 12),
          ErrorCard(error: error!, onRetry: _rank),
        ],
        if (result != null) ...[
          const SizedBox(height: 16),
          Text(
            '${result!['lead_count'] ?? 0} compatibility lead(s). '
            'Check each one against the source record.',
          ),
          const SizedBox(height: 8),
          for (final raw in (result!['leads'] as List? ?? const []))
            _LeadCard(lead: Map<String, dynamic>.from(raw as Map)),
        ],
        const SizedBox(height: 24),
        const Text(
          'Author Aziel Eliab. Apache-2.0. Forks welcome. Not a store IPA.',
        ),
      ],
    );
  }

  Widget _field(TextEditingController c, String label) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: c,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }
}

class _LeadCard extends StatelessWidget {
  const _LeadCard({required this.lead});
  final Map<String, dynamic> lead;

  @override
  Widget build(BuildContext context) {
    final fields = (lead['fields'] as List?) ?? const [];
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Compatibility lead'),
            const SizedBox(height: 8),
            Text('${lead['label'] ?? lead['notice_id']}', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              '${lead['event_class'] ?? ''} · ${lead['jurisdiction'] ?? ''}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: kGold),
            ),
            const SizedBox(height: 8),
            const Text('Check this lead against the source record before you treat it as the person.'),
            const SizedBox(height: 8),
            for (final raw in fields)
              Text(
                '${(raw as Map)['field']}: ${(raw)['status']} '
                '(${(raw)['subject']} / ${(raw)['notice']})',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            if ('${lead['next_verification'] ?? ''}'.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('${lead['next_verification']}'),
            ],
          ],
        ),
      ),
    );
  }
}
