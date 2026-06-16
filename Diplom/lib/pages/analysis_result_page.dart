import 'package:flutter/material.dart';

class AnalysisResultPage extends StatelessWidget {
  final double meanNdvi;
  final String vegetationStatus;
  final List<dynamic> history;
  final String? heatmapUrl;
  final String? rgbUrl;

  const AnalysisResultPage({
    super.key,
    required this.meanNdvi,
    required this.vegetationStatus,
    required this.history,
    this.heatmapUrl,
    this.rgbUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Результаты анализа"),
        backgroundColor: Colors.green,
      ),

      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),

        child: Column(
          children: [
            Container(
              width: double.infinity,

              padding: const EdgeInsets.all(16),

              decoration: BoxDecoration(
                border: Border.all(color: Colors.green),
                borderRadius: BorderRadius.circular(12),
              ),

              child: Column(
                children: [
                  Text(
                    "NDVI за последние 7 дней: ${meanNdvi.toStringAsFixed(3)}",
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 12),

                  Text(vegetationStatus, style: const TextStyle(fontSize: 18)),
                ],
              ),
            ),

            const SizedBox(height: 20),

            if (rgbUrl != null && heatmapUrl != null) ...[
              const Text(
                "Результаты спутникового анализа",
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 15),

              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        const Text(
                          "Исходный снимок",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),

                        const SizedBox(height: 8),

                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network(rgbUrl!, fit: BoxFit.cover),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: Column(
                      children: [
                        const Text(
                          "NDVI Heatmap",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),

                        const SizedBox(height: 8),

                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network(heatmapUrl!, fit: BoxFit.cover),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),
            ],

            const Text(
              "История NDVI",
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 10),

            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),

              itemCount: history.length,

              itemBuilder: (context, index) {
                final item = history[index];

                return Card(
                  child: ListTile(
                    leading: const Icon(Icons.show_chart),

                    title: Text("${item["start_date"]} - ${item["end_date"]}"),

                    subtitle: Text("Индекс растительности NDVI"),

                    trailing: Text(
                      "NDVI: ${item["ndvi"].toStringAsFixed(3)}",
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
