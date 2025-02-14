import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
        debugShowCheckedModeBanner: false, home: FirstPage());
  }
}

class FirstPage extends StatelessWidget {
  const FirstPage({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // DEBUG 배너 제거
      home: Scaffold(
        body: Container(
          width: double.infinity,
          height: double.infinity,
          decoration: const BoxDecoration(
            image: DecorationImage(
                image: AssetImage("assets/images/justLogoText.jpg"),
                fit: BoxFit.cover),
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const SizedBox(height: 30),
                const Spacer(),
                ClipRRect(
                  borderRadius: BorderRadius.circular(30),
                  child: Stack(
                    children: <Widget>[
                      Positioned.fill(
                        child: Container(
                          decoration: const BoxDecoration(
                            gradient: LinearGradient(
                              colors: <Color>[
                                Color(0xFF86A2F0), // 밝은 연보라색
                                Color(0xFFAE86F0), // 중간 연보라색
                                Color(0xFFEFACF5),
                              ],
                            ),
                          ),
                        ),
                      ),
                      TextButton(
                        style: TextButton.styleFrom(
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.all(15),
                            textStyle: const TextStyle(fontSize: 25),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(30),
                              side: const BorderSide(
                                  color: Colors.white, width: 2),
                            )),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) => const SecondScreen()),
                          );
                        },
                        child: const Text('Get Started'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 100),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SecondScreen extends StatefulWidget {
  const SecondScreen({super.key});

  @override
  _SecondScreenState createState() => _SecondScreenState();
}

class _SecondScreenState extends State<SecondScreen> {
  final TextEditingController _controller = TextEditingController();
  String _initialResponse = ''; // initial response를 위한 변수
  String _response = ''; // response를 위한 변수
  bool _isLoading = false; // 로딩 상태를 추적하는 변수

  Future<void> _getResponse() async {
    setState(() {
      _isLoading = true; // 전송 시작시 로딩 상태로 설정
    });

    final response = await http.post(
      Uri.parse('http://172.30.1.62:5000/ask'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'input': _controller.text,
      }),
    );

    if (response.statusCode == 200) {
      print("Response received: ${response.body}");
      setState(() {
        final jsonResponse = jsonDecode(response.body);
        // _initialResponse = jsonResponse['initial_response']; // initial_response 할당
        _response = jsonResponse['response']; // response 할당
        _isLoading = false; // 전송 완료시 로딩 상태 해제
      });
    } else {
      print("Failed to load response: ${response.statusCode}");
      setState(() {
        _initialResponse = 'Failed to load response'; // 에러 메시지 설정
        _response = '';
        _isLoading = false; // 전송 실패시 로딩 상태 해제
      });
      throw Exception('Failed to load response');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(''),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text(
              'MaiBle',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            const Text(
              '평소에 고민,문제 또는 궁금하신 성경 말씀을 질문해주세요.',
              style: TextStyle(fontSize: 18, color: Colors.grey),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Enter your text',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _getResponse,
              child: const Text('Submit'),
            ),
            const SizedBox(height: 20),
            _isLoading
                ? const CircularProgressIndicator()
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _initialResponse,
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _response,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
          ],
        ),
      ),
    );
  }
}
