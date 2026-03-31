import Foundation

struct RemoteConversationRepository: ConversationRepository {
    let endpoint: URL
    private let decoder = JSONDecoder()

    func loadThreads(page: ConversationPage) async throws -> ConversationPageResult {
        var components = URLComponents(url: endpoint, resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "limit", value: String(page.limit)),
            URLQueryItem(name: "cursor", value: page.cursor)
        ].compactMap { item in
            item.value == nil ? nil : item
        }
        guard let url = components?.url else {
            throw ConversationRepositoryError.invalidEndpoint
        }

        let (data, _) = try await URLSession.shared.data(from: url)
        let response = try decoder.decode(ThreadPageResponse.self, from: data)
        return response.page
    }
}

private struct ThreadPageResponse: Decodable {
    let page: ConversationPageResult
}

private enum ConversationRepositoryError: Error {
    case invalidEndpoint
}
