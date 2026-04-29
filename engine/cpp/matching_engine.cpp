#include "matching_engine.hpp"

#include <algorithm>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace nse::engine {

namespace {

std::string FormatTimestamp() {
  const auto now = std::chrono::system_clock::now();
  const std::time_t current_time = std::chrono::system_clock::to_time_t(now);
  std::tm utc_tm{};
#if defined(_WIN32)
  gmtime_s(&utc_tm, &current_time);
#else
  gmtime_r(&current_time, &utc_tm);
#endif
  std::ostringstream out;
  out << std::put_time(&utc_tm, "%Y-%m-%dT%H:%M:%SZ");
  return out.str();
}

bool IsBuy(const std::string& side) { return side == "BUY"; }

}  // namespace

bool OrderBook::IsCrossed(const Order& incoming, double best_price) const {
  if (incoming.order_type == "MARKET") {
    return true;
  }
  return IsBuy(incoming.side) ? best_price <= incoming.price : best_price >= incoming.price;
}

void OrderBook::RestOrder(const Order& order) {
  orders_[order.order_id] = order;
  if (IsBuy(order.side)) {
    bids_[order.price].push_back(order.order_id);
  } else {
    asks_[order.price].push_back(order.order_id);
  }
}

void OrderBook::RemoveFromLevel(const Order& order) {
  if (IsBuy(order.side)) {
    auto level_it = bids_.find(order.price);
    if (level_it == bids_.end()) {
      return;
    }
    auto& queue = level_it->second;
    queue.erase(std::remove(queue.begin(), queue.end(), order.order_id), queue.end());
    if (queue.empty()) {
      bids_.erase(level_it);
    }
  } else {
    auto level_it = asks_.find(order.price);
    if (level_it == asks_.end()) {
      return;
    }
    auto& queue = level_it->second;
    queue.erase(std::remove(queue.begin(), queue.end(), order.order_id), queue.end());
    if (queue.empty()) {
      asks_.erase(level_it);
    }
  }
}

SubmitResult OrderBook::Submit(Order incoming, const std::string& order_id, const std::string& trade_prefix, const std::string& timestamp) {
  incoming.order_id = order_id;
  incoming.remaining_qty = incoming.qty;
  incoming.timestamp = timestamp;
  std::vector<Trade> trades;
  if (IsBuy(incoming.side)) {
    while (incoming.remaining_qty > 0 && !asks_.empty()) {
      auto best_it = asks_.begin();
      const double best_price = best_it->first;
      if (!IsCrossed(incoming, best_price)) {
        break;
      }

      auto& queue = best_it->second;
      while (incoming.remaining_qty > 0 && !queue.empty()) {
        const auto resting_id = queue.front();
        auto resting_it = orders_.find(resting_id);
        if (resting_it == orders_.end()) {
          queue.pop_front();
          continue;
        }

        auto& resting = resting_it->second;
        const int fill_qty = std::min(incoming.remaining_qty, resting.remaining_qty);
        incoming.remaining_qty -= fill_qty;
        resting.remaining_qty -= fill_qty;

        Trade trade;
        trade.trade_id = trade_prefix + std::to_string(static_cast<int>(trades.size()) + 1);
        trade.symbol = symbol_;
        trade.price = resting.price;
        trade.qty = fill_qty;
        trade.taker_order_id = incoming.order_id;
        trade.maker_order_id = resting.order_id;
        trade.aggressor_side = incoming.side;
        trade.timestamp = timestamp;
        trades.push_back(trade);

        if (resting.remaining_qty == 0) {
          queue.pop_front();
          orders_.erase(resting_it);
        }
      }

      if (queue.empty()) {
        asks_.erase(best_it);
      }
    }
  } else {
    while (incoming.remaining_qty > 0 && !bids_.empty()) {
      auto best_it = bids_.begin();
      const double best_price = best_it->first;
      if (!IsCrossed(incoming, best_price)) {
        break;
      }

      auto& queue = best_it->second;
      while (incoming.remaining_qty > 0 && !queue.empty()) {
        const auto resting_id = queue.front();
        auto resting_it = orders_.find(resting_id);
        if (resting_it == orders_.end()) {
          queue.pop_front();
          continue;
        }

        auto& resting = resting_it->second;
        const int fill_qty = std::min(incoming.remaining_qty, resting.remaining_qty);
        incoming.remaining_qty -= fill_qty;
        resting.remaining_qty -= fill_qty;

        Trade trade;
        trade.trade_id = trade_prefix + std::to_string(static_cast<int>(trades.size()) + 1);
        trade.symbol = symbol_;
        trade.price = resting.price;
        trade.qty = fill_qty;
        trade.taker_order_id = incoming.order_id;
        trade.maker_order_id = resting.order_id;
        trade.aggressor_side = incoming.side;
        trade.timestamp = timestamp;
        trades.push_back(trade);

        if (resting.remaining_qty == 0) {
          queue.pop_front();
          orders_.erase(resting_it);
        }
      }

      if (queue.empty()) {
        bids_.erase(best_it);
      }
    }
  }

  const int filled_qty = incoming.qty - incoming.remaining_qty;
  if (incoming.remaining_qty > 0 && incoming.order_type == "LIMIT") {
    RestOrder(incoming);
  }
  if (incoming.order_type == "MARKET") {
    incoming.remaining_qty = 0;
  }

  SubmitResult result;
  result.order = incoming;
  result.trades = trades;
  result.status = filled_qty == incoming.qty ? "FILLED" : (filled_qty > 0 ? "PARTIAL" : "ACCEPTED");
  result.snapshot = BuildSnapshot(5, timestamp);
  return result;
}

SubmitResult OrderBook::Cancel(const std::string& order_id, const std::string& owner, const std::string& timestamp) {
  SubmitResult result;
  auto order_it = orders_.find(order_id);
  if (order_it == orders_.end()) {
    result.status = "MISSING";
    result.snapshot = BuildSnapshot(5, timestamp);
    return result;
  }

  Order order = order_it->second;
  orders_.erase(order_it);
  RemoveFromLevel(order);
  order.remaining_qty = 0;
  order.owner = owner;
  order.timestamp = timestamp;

  result.order = order;
  result.status = "CANCELLED";
  result.snapshot = BuildSnapshot(5, timestamp);
  return result;
}

Snapshot OrderBook::BuildSnapshot(int depth, const std::string& timestamp) const {
  Snapshot snapshot;
  snapshot.symbol = symbol_;
  snapshot.timestamp = timestamp;

  int count = 0;
  for (const auto& [price, queue] : bids_) {
    if (count++ >= depth) {
      break;
    }
    int qty = 0;
    for (const auto& order_id : queue) {
      auto it = orders_.find(order_id);
      if (it != orders_.end()) {
        qty += it->second.remaining_qty;
      }
    }
    if (qty > 0) {
      snapshot.bids.push_back({price, qty});
    }
  }

  count = 0;
  for (const auto& [price, queue] : asks_) {
    if (count++ >= depth) {
      break;
    }
    int qty = 0;
    for (const auto& order_id : queue) {
      auto it = orders_.find(order_id);
      if (it != orders_.end()) {
        qty += it->second.remaining_qty;
      }
    }
    if (qty > 0) {
      snapshot.asks.push_back({price, qty});
    }
  }

  if (!snapshot.bids.empty()) {
    snapshot.has_best_bid = true;
    snapshot.best_bid = snapshot.bids.front().price;
  }
  if (!snapshot.asks.empty()) {
    snapshot.has_best_ask = true;
    snapshot.best_ask = snapshot.asks.front().price;
  }
  return snapshot;
}

OrderBook& MatchingEngine::BookFor(const std::string& symbol) {
  auto it = books_.find(symbol);
  if (it == books_.end()) {
    it = books_.emplace(symbol, std::make_unique<OrderBook>(symbol)).first;
  }
  return *it->second;
}

std::string MatchingEngine::NextOrderId() {
  ++order_sequence_;
  std::ostringstream out;
  out << 'O' << std::setw(7) << std::setfill('0') << order_sequence_;
  return out.str();
}

std::string MatchingEngine::TradePrefix() {
  ++trade_sequence_;
  std::ostringstream out;
  out << 'T' << std::setw(6) << std::setfill('0') << trade_sequence_ << '-';
  return out.str();
}

std::string MatchingEngine::UtcNowIso() { return FormatTimestamp(); }

SubmitResult MatchingEngine::Submit(const std::string& symbol,
                                    const std::string& side,
                                    const std::string& order_type,
                                    double price,
                                    int qty,
                                    const std::string& owner,
                                    const std::string& strategy_id) {
  Order order;
  order.symbol = symbol;
  order.side = side;
  order.order_type = order_type;
  order.price = price;
  order.qty = qty;
  order.owner = owner;
  order.strategy_id = strategy_id;
  return BookFor(symbol).Submit(order, NextOrderId(), TradePrefix(), UtcNowIso());
}

SubmitResult MatchingEngine::Cancel(const std::string& symbol, const std::string& order_id, const std::string& owner) {
  return BookFor(symbol).Cancel(order_id, owner, UtcNowIso());
}

Snapshot MatchingEngine::SnapshotFor(const std::string& symbol, int depth) const {
  auto it = books_.find(symbol);
  if (it == books_.end()) {
    Snapshot empty;
    empty.symbol = symbol;
    empty.timestamp = UtcNowIso();
    return empty;
  }
  return it->second->BuildSnapshot(depth, UtcNowIso());
}

void MatchingEngine::Reset() {
  books_.clear();
  order_sequence_ = 0;
  trade_sequence_ = 0;
}

}  // namespace nse::engine
