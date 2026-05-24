// Map of slug → case study component.
// Add a project here when you add it to content/projects.ts.

import ChannelStream from "./channel-stream";
import AwsComplianceCollector from "./aws-compliance-collector";
import ApexBenchmark from "./apex-benchmark";
import NcLaborMarket from "./nc-labor-market";
import GtmCalculator from "./gtm-calculator";
import DataScienceNotebooks from "./data-science-notebooks";

export const caseStudies = {
  "channel-stream": ChannelStream,
  "aws-compliance-collector": AwsComplianceCollector,
  "apex-benchmark": ApexBenchmark,
  "nc-labor-market": NcLaborMarket,
  "gtm-calculator": GtmCalculator,
  "data-science-notebooks": DataScienceNotebooks,
} as const;
