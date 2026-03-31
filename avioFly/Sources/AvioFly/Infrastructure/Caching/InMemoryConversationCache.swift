import Foundation

actor InMemoryConversationCache: ConversationCache {
    private var threadCache: [String: ConversationPageResult] = [:]
    private var responseCache: [String: ChatResponse] = [:]
    private let maxCachedEntries = 50

    func cachedThreads(for page: ConversationPage) async -> ConversationPageResult? {
        threadCache[cacheKey(for: page)]
    }

    func storeThreads(_ result: ConversationPageResult, for page: ConversationPage) async {
        threadCache[cacheKey(for: page)] = result
        trimIfNeeded(&threadCache)
    }

    func cachedResponse(for key: String) async -> ChatResponse? {
        responseCache[key]
    }

    func storeResponse(_ response: ChatResponse, for key: String) async {
        responseCache[key] = response
        trimIfNeeded(&responseCache)
    }

    private func cacheKey(for page: ConversationPage) -> String {
        "\(page.cursor ?? "root")::\(page.limit)"
    }

    private func trimIfNeeded<Value>(_ cache: inout [String: Value]) {
        guard cache.count > maxCachedEntries else { return }
        // Bounded on purpose so repeated chat sessions do not keep growing memory use.
        cache = Dictionary(uniqueKeysWithValues: cache.prefix(maxCachedEntries))
    }
}
