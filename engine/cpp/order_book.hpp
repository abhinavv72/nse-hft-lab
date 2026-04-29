#pragma once

#include <algorithm>
#include <deque>
#include <functional>
#include <map>
#include <string>
#include <unordered_map>

#include "order.hpp"
#include "trade.hpp"

namespace nse::engine {

class OrderBook {
 public:
  explicit OrderBook(std::string symbol) : symbol_(std::move(symbol)) {}

  SubmitResult Submit(Order incoming, const std::string& order_id, const std::string& trade_prefix, const std::string& timestamp);
  SubmitResult Cancel(const std::string& order_id, const std::string& owner, const std::string& timestamp);
  Snapshot BuildSnapshot(int depth, const std::string& timestamp) const;

 private:
  // Price levels map to FIFO queues of order ids, preserving price-time priority.
  std::map<double, std::deque<std::string>, std::greater<>> bids_;
  std::map<double, std::deque<std::string>, std::less<>> asks_;
  std::unordered_map<std::string, Order> orders_;
  std::string symbol_;

  bool IsCrossed(const Order& incoming, double best_price) const;
  void RestOrder(const Order& order);
  void RemoveFromLevel(const Order& order);
};

}  // namespace nse::engine
