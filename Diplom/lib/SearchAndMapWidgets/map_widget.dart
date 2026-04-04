import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class MapWidget extends StatelessWidget {
  final MapController mapController;
  final List<LatLng> points;
  final Function(LatLng) onTap;

  const MapWidget({
    super.key,
    required this.mapController,
    required this.points,
    required this.onTap,
  });

  @override
  //Карта
  Widget build(BuildContext context) {
    return Expanded(
      child: Center(
        child: Container(
          width: 800,
          height: 500,
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey),
            borderRadius: BorderRadius.circular(12),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: FlutterMap(
              mapController: mapController,
              options: MapOptions(
                initialCenter: LatLng(56.95, 24.10),
                initialZoom: 10,
                onTap: (_, pos) => onTap(pos),
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.myapp',
                ),

                /// 📍 точки
                MarkerLayer(
                  markers: points.map((p) {
                    return Marker(
                      point: p,
                      width: 40,
                      height: 40,
                      child: const Icon(Icons.location_pin, color: Colors.red),
                    );
                  }).toList(),
                ),

                /// 🟩 полигон
                PolygonLayer(
                  polygons: [
                    if (points.length >= 3)
                      Polygon(
                        points: points,
                        color: Colors.green.withOpacity(0.3),
                        borderColor: Colors.green,
                        borderStrokeWidth: 3,
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
