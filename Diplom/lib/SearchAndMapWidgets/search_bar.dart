import 'package:flutter/material.dart';

class SearchBarWidget extends StatelessWidget {
  final TextEditingController controller;
  final Function(String) onChanged;
  final VoidCallback onSearch;

  const SearchBarWidget({
    super.key,
    required this.controller,
    required this.onChanged,
    required this.onSearch,
  });

  @override
  //Поле поиска
  Widget build(BuildContext context) {
    //Поиск
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              onChanged: onChanged,
              decoration: const InputDecoration(
                hintText: "Введите место",
                border: OutlineInputBorder(),
              ),
            ),
          ),
          IconButton(icon: const Icon(Icons.search), onPressed: onSearch),
        ],
      ),
    );
  }
}
