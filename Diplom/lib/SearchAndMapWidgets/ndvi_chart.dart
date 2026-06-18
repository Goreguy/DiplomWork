import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

class NdviChart extends StatelessWidget {
  final List<dynamic> history;
  final double? cnnNdvi;

  const NdviChart({super.key, required this.history, this.cnnNdvi});

  double _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value.toString()) ?? 0.0;
  }

  @override
  Widget build(BuildContext context) {
    final orderedHistory = history.reversed.toList();

    final spots = <FlSpot>[];

    for (int i = 0; i < orderedHistory.length; i++) {
      spots.add(FlSpot(i.toDouble(), _toDouble(orderedHistory[i]["ndvi"])));
    }

    final hasCnnPoint = cnnNdvi != null && spots.isNotEmpty;

    // CNN-точка ставится НЕ поверх последней NDVI-точки,
    // а отдельной точкой справа, чтобы она не соединялась с основной линией.
    final double cnnX = hasCnnPoint ? spots.length.toDouble() : 0.0;

    final List<LineChartBarData> lines = [
      LineChartBarData(
        spots: spots,
        isCurved: true,
        barWidth: 3,
        dotData: FlDotData(
          show: true,
          getDotPainter: (spot, percent, barData, index) {
            return FlDotCirclePainter(
              radius: 3.5,
              color: const Color(0xFF4CAF50),
              strokeWidth: 1.5,
              strokeColor: Colors.white,
            );
          },
        ),
      ),
    ];

    if (hasCnnPoint) {
      lines.add(
        LineChartBarData(
          spots: [FlSpot(cnnX, cnnNdvi!)],
          isCurved: false,

          // Линию не рисуем, только точку.
          barWidth: 0,
          color: Colors.transparent,

          dotData: FlDotData(
            show: true,
            getDotPainter: (spot, percent, barData, index) {
              return FlDotCirclePainter(
                radius: 6,
                color: const Color(0xFFE91E63), // розовый под интерфейс
                strokeWidth: 2,
                strokeColor: Colors.white,
              );
            },
          ),
        ),
      );
    }

    return SizedBox(
      height: 320,
      child: Padding(
        // Дополнительные отступы, чтобы подписи и tooltip не резались краями.
        padding: const EdgeInsets.only(left: 8, right: 18, top: 16, bottom: 8),
        child: LineChart(
          LineChartData(
            minX: -0.2,
            maxX: hasCnnPoint ? cnnX + 0.35 : spots.length.toDouble() - 1,
            minY: 0,
            maxY: 1,

            lineBarsData: lines,

            lineTouchData: LineTouchData(
              handleBuiltInTouches: true,
              touchTooltipData: LineTouchTooltipData(
                fitInsideHorizontally: true,
                fitInsideVertically: true,
                tooltipPadding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 8,
                ),
                getTooltipItems: (touchedSpots) {
                  return touchedSpots.map((spot) {
                    final bool isCnnPoint =
                        hasCnnPoint &&
                        (spot.x - cnnX).abs() < 0.001 &&
                        (spot.y - cnnNdvi!).abs() < 0.001;

                    return LineTooltipItem(
                      isCnnPoint
                          ? "CNN NDVI: ${spot.y.toStringAsFixed(3)}"
                          : "NDVI: ${spot.y.toStringAsFixed(3)}",
                      TextStyle(
                        color: isCnnPoint
                            ? const Color(0xFFFFC1D6)
                            : Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    );
                  }).toList();
                },
              ),
            ),

            titlesData: FlTitlesData(
              topTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),
              rightTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: false),
              ),

              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  interval: 0.2,
                  reservedSize: 44,
                  getTitlesWidget: (value, meta) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 4),
                      child: Text(
                        value.toStringAsFixed(3),
                        style: const TextStyle(fontSize: 10),
                      ),
                    );
                  },
                ),
              ),

              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  interval: 1,
                  reservedSize: 34,
                  getTitlesWidget: (value, meta) {
                    final index = value.toInt();

                    if (hasCnnPoint && (value - cnnX).abs() < 0.001) {
                      return const Padding(
                        padding: EdgeInsets.only(top: 6),
                        child: Text(
                          "CNN",
                          style: TextStyle(
                            fontSize: 10,
                            color: Color(0xFFE91E63),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      );
                    }

                    if (index < 0 || index >= orderedHistory.length) {
                      return const SizedBox();
                    }

                    final date = orderedHistory[index]["end_date"].toString();

                    return Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        date.length >= 10 ? date.substring(5) : date,
                        style: const TextStyle(fontSize: 10),
                      ),
                    );
                  },
                ),
              ),
            ),

            gridData: const FlGridData(show: true),

            borderData: FlBorderData(
              show: true,
              border: Border.all(color: Colors.black12),
            ),
          ),
        ),
      ),
    );
  }
}
