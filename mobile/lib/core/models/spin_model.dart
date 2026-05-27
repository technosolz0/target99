class SpinResultModel {
  final int id;
  final double betAmount;
  final double multiplier;
  final double winAmount;
  final String resultType;
  final String wheelSegment;
  final int segmentIndex;
  final DateTime createdAt;
  final double updatedBalance;

  SpinResultModel({
    required this.id,
    required this.betAmount,
    required this.multiplier,
    required this.winAmount,
    required this.resultType,
    required this.wheelSegment,
    required this.segmentIndex,
    required this.createdAt,
    required this.updatedBalance,
  });

  factory SpinResultModel.fromJson(Map<String, dynamic> json) {
    return SpinResultModel(
      id: json['id'] as int,
      betAmount: (json['bet_amount'] as num).toDouble(),
      multiplier: (json['multiplier'] as num).toDouble(),
      winAmount: (json['win_amount'] as num).toDouble(),
      resultType: json['result_type'] as String,
      wheelSegment: json['wheel_segment'] as String,
      segmentIndex: json['segment_index'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedBalance: (json['updated_balance'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'bet_amount': betAmount,
      'multiplier': multiplier,
      'win_amount': winAmount,
      'result_type': resultType,
      'wheel_segment': wheelSegment,
      'segment_index': segmentIndex,
      'created_at': createdAt.toIso8601String(),
      'updated_balance': updatedBalance,
    };
  }
}
