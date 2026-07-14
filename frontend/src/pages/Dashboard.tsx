import { PipelineViz } from "../components/PipelineViz/PipelineViz";
import { PortfolioRisk } from "../components/PortfolioRisk/PortfolioRisk";
import { RecommendationList } from "../components/RecommendationCard/RecommendationCard";
import { ResearchQuality } from "../components/ResearchQuality/ResearchQuality";
import { SignalFeed } from "../components/SignalFeed/SignalFeed";
import { SystemStatus } from "../components/SystemStatus/SystemStatus";

export function Dashboard() {
  return (
    <div className="space-y-8">
      <SystemStatus />
      <ResearchQuality />
      <PortfolioRisk />
      <PipelineViz />
      <SignalFeed />
      <section aria-labelledby="rec-heading">
        <h2 id="rec-heading" className="mb-3 text-xl font-semibold">
          Pending Recommendations
        </h2>
        <RecommendationList />
      </section>
    </div>
  );
}
