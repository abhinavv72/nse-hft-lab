#pragma once

#include <memory>
#include <string>
#include <unordered_map>

#include "order_book.hpp"

namespace nse::engine {

class MatchingEngine {
 public:
  SubmitResult Submit(const std::string& symbol,
                      const std::string& side,
                      const std::string& order_type,
                      double price,
                      int qty,
                      const std::string& owner,
                      const std::string& strategy_id);

  SubmitResult Cancel(const std::string& symbol, const std::string& order_id, const std::string& owner);
  Snapshot SnapshotFor(const std::string& symbol, int depth) const;
  void Reset();

 private:
  OrderBook& BookFor(const std::string& symbol);
  mutable int order_sequence_{0};
  mutable int trade_sequence_{0};
  std::unordered_map<std::string, std::unique_ptr<OrderBook>> books_;

  std::string NextOrderId();
  std::string TradePrefix();
  static std::string UtcNowIso();
};

}  // namespace nse::engine
