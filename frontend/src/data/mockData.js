export const mockAnalysis = {
  temperature: {
    degradation: {
      1: 0.31, 2: 0.38, 3: 0.45, 4: 0.52, 5: 0.58,
      6: 0.63, 7: 0.69, 8: 0.74, 9: 0.79, 10: 0.83,
      11: 0.87, 12: 0.91, 13: 0.95, 14: 0.99, 15: 1.03,
      16: 1.07, 17: 1.11, 18: 1.15, 19: 1.18, 20: 1.21,
      21: 1.24, 22: 1.27, 23: 1.30, 24: 1.33, 25: 1.36,
      26: 1.38, 27: 1.40, 28: 1.42, 29: 1.44, 30: 1.46,
      31: 1.48, 32: 1.50, 33: 1.52, 34: 1.54, 35: 1.56,
      36: 1.57, 37: 1.58, 38: 1.59, 39: 1.60, 40: 1.61,
      41: 1.62, 42: 1.63, 43: 1.64, 44: 1.65, 45: 1.66,
      46: 1.67, 47: 1.68, 48: 1.69,
    }
  },
  rain: {
    tp: 18, fp: 24, fn: 6, tn: 112,
    precision: 0.43, recall: 0.75, f1: 0.54,
    insight: "The model tends to over-predict rain — 24 false alarms across the period."
  },
  sunshine: {
    tp: 87, fp: 12, fn: 8, tn: 53,
    precision: 0.88, recall: 0.92, f1: 0.90,
    insight: "Sunshine is well captured across the period with strong precision and recall."
  }
}