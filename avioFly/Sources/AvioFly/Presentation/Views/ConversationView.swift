import SwiftUI

struct ConversationView: View {
    @StateObject private var viewModel: ConversationViewModel
    @State private var draftMessage: String = ""
    @State private var selectedMode: ConversationMode = .concierge

    init(viewModel: ConversationViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            ZStack {
                background
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        heroSection
                        metricsStrip
                        insightGrid
                        threadSection
                        chatSection
                        artifactSection
                    }
                    .padding()
                }
            }
            .navigationTitle("Conversation")
            .task {
                await viewModel.loadDashboard()
            }
        }
    }

    private var background: some View {
        LinearGradient(
            colors: [Color.black.opacity(0.95), Color.blue.opacity(0.35), Color.cyan.opacity(0.20)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var heroSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Conversation")
                        .font(.largeTitle.bold())
                    Text("AI Conversation Layer")
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(.secondary)
                }
                Spacer()
                OperationalModePillView(mode: viewModel.activeMode)
            }

            Text("A production-grade chat module with backend-agnostic AI orchestration, structured responses, and a clean injection boundary for a host app.")
                .font(.subheadline)
                .foregroundStyle(.secondary)

                HStack(spacing: 12) {
                    IntelligenceBadgeView(title: "AI State", value: "Operational", tint: .green)
                    IntelligenceBadgeView(title: "Model Layer", value: "Swappable Service", tint: .cyan)
                    IntelligenceBadgeView(title: "Paging", value: viewModel.hasMoreThreads ? "Enabled" : "Complete", tint: .orange)
                }
        }
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28))
    }

    private var metricsStrip: some View {
        HStack(spacing: 12) {
            IntelligenceBadgeView(title: "Confidence", value: "\(viewModel.assistantConfidence * 100, specifier: "%.0f")%", tint: .green)
            IntelligenceBadgeView(title: "Mode", value: viewModel.activeMode.rawValue.capitalized, tint: .blue)
            IntelligenceBadgeView(title: "Signals", value: "\(viewModel.artifacts.count)", tint: .orange)
        }
    }

    private var insightGrid: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Conversation Intelligence")
                .font(.headline)
                .foregroundStyle(.white)

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Reasoning Summary")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(viewModel.reasoningSummary)
                        .font(.body)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))

                VStack(alignment: .leading, spacing: 8) {
                    Text("Safety & Governance")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(viewModel.safetyNotice ?? "Awaiting policy context.")
                        .font(.body)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
            }
        }
    }

    private var threadSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Conversation History")
                    .font(.headline)
                    .foregroundStyle(.white)
                Spacer()
                if viewModel.isLoadingMore {
                    ProgressView()
                } else if viewModel.hasMoreThreads {
                    Button("Load More") {
                        Task { await viewModel.loadMoreThreads() }
                    }
                    .buttonStyle(.bordered)
                }
            }

            if viewModel.isLoading {
                ProgressView("Loading history")
                    .padding(.vertical, 4)
            }

            if viewModel.threads.isEmpty {
                Text("No prior threads available.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.threads) { thread in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(thread.title)
                            .font(.headline)
                        Text(thread.preview ?? "No preview available.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
                }
            }
        }
    }

    private var chatSection: some View {
        VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("AI Decision Console")
                        .font(.headline)
                        .foregroundStyle(.white)
                    Spacer()
                    Picker("Mode", selection: $selectedMode) {
                        Text("Concierge").tag(ConversationMode.concierge)
                        Text("Support").tag(ConversationMode.support)
                        Text("Expert").tag(ConversationMode.expert)
                    }
                    .pickerStyle(.menu)
                }

            if viewModel.isSendingMessage {
                HStack {
                    ProgressView("Processing")
                    Spacer()
                    Button("Cancel") {
                        viewModel.cancelCurrentSend()
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.vertical, 4)
            }

            if viewModel.messages.isEmpty {
                Text("Conversation will appear here once the backend is connected.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(viewModel.messages) { message in
                    ConversationBubbleView(message: message)
                }
            }

            if viewModel.currentResponseKind == .options || viewModel.currentResponseKind == .mixed {
                optionsSection
            }

            VStack(alignment: .leading, spacing: 10) {
                TextField("Ask a question or request a response", text: $draftMessage)
                    .textFieldStyle(.roundedBorder)
                HStack {
                    Button("Generate briefing") {
                        draftMessage = "Create a concise response template for a user support request."
                    }
                    .buttonStyle(.bordered)

                    Spacer()

                    Button("Send") {
                        let message = draftMessage
                        draftMessage = ""
                        viewModel.selectMode(selectedMode)
                        Task { await viewModel.sendMessage(message) }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(viewModel.isSendingMessage)
                }
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
            }
        }
    }

    private var optionsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Choose a response")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)

            ForEach(viewModel.currentOptions) { option in
                Button {
                    Task { await viewModel.sendOption(option) }
                } label: {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(option.title)
                                .font(.body.weight(.semibold))
                            Text(option.value)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var artifactSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Trace Artifacts")
                .font(.headline)
                .foregroundStyle(.white)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(viewModel.artifacts) { artifact in
                    IntelligenceArtifactCardView(artifact: artifact)
                }
            }

            if !viewModel.suggestedActions.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Suggested Actions")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(viewModel.suggestedActions, id: \.self) { action in
                                Text(action)
                                    .font(.caption)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .background(.thinMaterial, in: Capsule())
                            }
                        }
                    }
                }
            }
        }
    }
}
