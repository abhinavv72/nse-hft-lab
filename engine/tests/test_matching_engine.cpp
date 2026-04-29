#include <cassert>
#include <iostream>

#include "matching_engine.hpp"

int main() {
  nse::engine::MatchingEngine engine;

  const auto buy1 = engine.Submit("NIFTY", "BUY", "LIMIT", 22000.0, 10, "test", "");
  assert(buy1.order.order_id == "O0000001");
  assert(buy1.snapshot.has_best_bid);
  assert(buy1.snapshot.best_bid == 22000.0);

  const auto buy2 = engine.Submit("NIFTY", "BUY", "LIMIT", 22000.0, 5, "test", "");
  assert(buy2.order.order_id == "O0000002");

  const auto sell = engine.Submit("NIFTY", "SELL", "LIMIT", 22000.0, 12, "test", "");
  assert(sell.trades.size() == 2);
  assert(sell.trades.front().maker_order_id == "O0000001");
  assert(sell.trades.back().maker_order_id == "O0000002");

  const auto snapshot = engine.SnapshotFor("NIFTY", 5);
  assert(snapshot.has_best_bid);
  assert(snapshot.best_bid == 22000.0);
  assert(snapshot.bids.front().qty == 3);

  const auto cancel = engine.Cancel("NIFTY", "O0000002", "test");
  assert(cancel.status == "CANCELLED");
  const auto final_snapshot = engine.SnapshotFor("NIFTY", 5);
  assert(!final_snapshot.has_best_bid);

  std::cout << "matching_engine_tests_passed\n";
  return 0;
}
