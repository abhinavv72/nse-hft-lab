#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "matching_engine.hpp"

namespace {

std::vector<std::string> Split(const std::string& input, char delimiter) {
  std::vector<std::string> parts;
  std::stringstream stream(input);
  std::string token;
  while (std::getline(stream, token, delimiter)) {
    parts.push_back(token);
  }
  return parts;
}

std::string Quote(const std::string& value) { return "\"" + value + "\""; }

std::string OrderJson(const nse::engine::Order& order, const std::string& status) {
  std::ostringstream out;
  out << "{"
      << "\"order_id\":" << Quote(order.order_id) << ","
      << "\"symbol\":" << Quote(order.symbol) << ","
      << "\"side\":" << Quote(order.side) << ","
      << "\"order_type\":" << Quote(order.order_type) << ","
      << "\"price\":" << order.price << ","
      << "\"qty\":" << order.qty << ","
      << "\"remaining_qty\":" << order.remaining_qty << ","
      << "\"filled_qty\":" << (order.qty - order.remaining_qty) << ","
      << "\"status\":" << Quote(status) << ","
      << "\"owner\":" << Quote(order.owner) << ","
      << "\"strategy_id\":" << (order.strategy_id.empty() ? "null" : Quote(order.strategy_id)) << ","
      << "\"timestamp\":" << Quote(order.timestamp)
      << "}";
  return out.str();
}

std::string TradeJson(const nse::engine::Trade& trade) {
  std::ostringstream out;
  out << "{"
      << "\"trade_id\":" << Quote(trade.trade_id) << ","
      << "\"symbol\":" << Quote(trade.symbol) << ","
      << "\"price\":" << trade.price << ","
      << "\"qty\":" << trade.qty << ","
      << "\"taker_order_id\":" << Quote(trade.taker_order_id) << ","
      << "\"maker_order_id\":" << Quote(trade.maker_order_id) << ","
      << "\"aggressor_side\":" << Quote(trade.aggressor_side) << ","
      << "\"timestamp\":" << Quote(trade.timestamp) << ","
      << "\"source_owner\":null"
      << "}";
  return out.str();
}

std::string SnapshotJson(const nse::engine::Snapshot& snapshot) {
  std::ostringstream out;
  out << "{"
      << "\"symbol\":" << Quote(snapshot.symbol) << ","
      << "\"bids\":[";
  for (std::size_t i = 0; i < snapshot.bids.size(); ++i) {
    if (i > 0) {
      out << ",";
    }
    out << "{\"price\":" << snapshot.bids[i].price << ",\"qty\":" << snapshot.bids[i].qty << "}";
  }
  out << "],\"asks\":[";
  for (std::size_t i = 0; i < snapshot.asks.size(); ++i) {
    if (i > 0) {
      out << ",";
    }
    out << "{\"price\":" << snapshot.asks[i].price << ",\"qty\":" << snapshot.asks[i].qty << "}";
  }
  out << "],"
      << "\"best_bid\":" << (snapshot.has_best_bid ? std::to_string(snapshot.best_bid) : "null") << ","
      << "\"best_ask\":" << (snapshot.has_best_ask ? std::to_string(snapshot.best_ask) : "null") << ","
      << "\"timestamp\":" << Quote(snapshot.timestamp)
      << "}";
  return out.str();
}

}  // namespace

int main() {
  std::cout << std::unitbuf;
  nse::engine::MatchingEngine engine;
  std::string line;
  while (std::getline(std::cin, line)) {
    if (line == "STOP") {
      break;
    }
    if (line == "RESET") {
      engine.Reset();
      std::cout << "SNAPSHOT\t{\"symbol\":\"RESET\",\"bids\":[],\"asks\":[],\"best_bid\":null,\"best_ask\":null,\"timestamp\":\"\"}\n";
      std::cout << "END\n";
      continue;
    }

    const auto parts = Split(line, '\t');
    if (parts.empty()) {
      continue;
    }

    if (parts[0] == "SUBMIT" && parts.size() >= 7) {
      const std::string strategy_id = parts.size() >= 8 ? parts[7] : "";
      const auto result = engine.Submit(parts[1], parts[2], parts[3], std::stod(parts[4]), std::stoi(parts[5]), parts[6], strategy_id);
      std::cout << "ORDER\t" << OrderJson(result.order, result.status) << "\n";
      for (const auto& trade : result.trades) {
        std::cout << "TRADE\t" << TradeJson(trade) << "\n";
      }
      std::cout << "SNAPSHOT\t" << SnapshotJson(result.snapshot) << "\n";
      std::cout << "END\n";
      continue;
    }

    if (parts[0] == "CANCEL" && parts.size() >= 4) {
      const auto result = engine.Cancel(parts[1], parts[2], parts[3]);
      if (!result.order.order_id.empty()) {
        std::cout << "ORDER\t" << OrderJson(result.order, result.status) << "\n";
      }
      std::cout << "SNAPSHOT\t" << SnapshotJson(result.snapshot) << "\n";
      std::cout << "END\n";
      continue;
    }

    if (parts[0] == "SNAPSHOT" && parts.size() >= 3) {
      const auto snapshot = engine.SnapshotFor(parts[1], std::stoi(parts[2]));
      std::cout << "SNAPSHOT\t" << SnapshotJson(snapshot) << "\n";
      std::cout << "END\n";
    }
  }
  return 0;
}
