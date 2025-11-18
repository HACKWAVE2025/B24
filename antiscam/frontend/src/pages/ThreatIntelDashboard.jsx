import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import Sidebar from '@/components/Sidebar';
import TopNav from '@/components/TopNav';
import ThreatReceiverCard from '@/components/threat-intel/ThreatReceiverCard';
import ClusterCard from '@/components/threat-intel/ClusterCard';
import ThreatTimeline from '@/components/threat-intel/ThreatTimeline';
import { getThreatIntelGlobal, getThreatIntelClusters, getReceiverThreatIntel } from '@/services/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { RefreshCcw } from 'lucide-react';

const ThreatIntelDashboard = ({ onLogout, darkMode, toggleDarkMode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [trending, setTrending] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedReceiver, setSelectedReceiver] = useState(null);
  const [timelineState, setTimelineState] = useState({ loading: false, history: [], error: null });

  const fetchThreatIntel = async () => {
    try {
      setLoading(true);
      setError(null);
      const [globalResponse, clustersResponse] = await Promise.all([
        getThreatIntelGlobal(),
        getThreatIntelClusters(),
      ]);

      const sortedTrending = (globalResponse?.trending || [])
        .sort((a, b) => (b.threat_score ?? b.threatScore ?? 0) - (a.threat_score ?? a.threatScore ?? 0))
        .slice(0, 10);

      const clusterList = (clustersResponse?.clusters || globalResponse?.clusters || []).map((cluster) => {
        const memberCount = cluster.count ?? cluster.size ?? cluster.members?.length ?? cluster.receivers?.length ?? 0;
        return {
          ...cluster,
          avgScore: cluster.avgScore ?? cluster.avg_score ?? 0,
          count: memberCount,
          topKeywords: cluster.topKeywords || cluster.top_keywords || [],
          updatedAt: cluster.updatedAt || cluster.updated_at,
          active: cluster.active !== false,
        };
      });

      setTrending(sortedTrending);
      setClusters(clusterList);
    } catch (err) {
      console.error('Threat intel fetch failed', err);
      setError('Unable to load threat intelligence data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreatIntel();
  }, []);

  const { emergingClusters, activeClusters, inactiveClusters } = useMemo(() => {
    const now = Date.now();
    const emergingThreshold = 1000 * 60 * 60 * 24 * 7; // 7 days
    const emerging = [];
    const active = [];
    const inactive = [];

    clusters.forEach((cluster) => {
      const updatedMs = cluster.updatedAt ? new Date(cluster.updatedAt).getTime() : 0;
      const isEmerging = Boolean(updatedMs && now - updatedMs <= emergingThreshold);
      const enrichedCluster = { ...cluster, isEmerging };

      if (!cluster.active) {
        inactive.push(enrichedCluster);
      } else if (isEmerging) {
        emerging.push(enrichedCluster);
      } else {
        active.push(enrichedCluster);
      }
    });

    return { emergingClusters: emerging, activeClusters: active, inactiveClusters: inactive };
  }, [clusters]);

  const receiverClusterMap = useMemo(() => {
    const map = {};
    clusters.forEach((cluster) => {
      (cluster.members || cluster.receivers || []).forEach((receiver) => {
        map[receiver] = cluster.name;
      });
    });
    return map;
  }, [clusters]);

  const handleReceiverSelect = async (receiver) => {
    setSelectedReceiver(receiver);
    setSheetOpen(true);
    setTimelineState({ loading: true, history: [], error: null });

    try {
      const data = await getReceiverThreatIntel(receiver);
      setTimelineState({
        loading: false,
        history: data?.history || [],
        error: null,
      });
    } catch (err) {
      console.error('Receiver intel fetch failed', err);
      setTimelineState({
        loading: false,
        history: [],
        error: 'Unable to load receiver timeline.',
      });
    }
  };

  const renderClusterGrid = (items, emptyMessage, columnClasses = 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6') => {
    if (!items.length) {
      return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
    }
    return (
      <div className={columnClasses}>
        {items.map((cluster, index) => (
          <ClusterCard
            key={cluster.clusterId || `${cluster.name}-${index}`}
            cluster={cluster}
            delay={index * 0.05}
          />
        ))}
      </div>
    );
  };

  return (
    <div className={darkMode ? 'min-h-screen bg-gray-900' : 'min-h-screen bg-[#F8FAFB]'}>
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={onLogout} />
      <TopNav onMenuClick={() => setSidebarOpen(true)} darkMode={darkMode} onDarkModeToggle={toggleDarkMode} />

      <section className="pt-24 pb-20 px-6">
        <div className="max-w-7xl mx-auto space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col gap-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h1 className={darkMode ? "text-4xl font-bold text-white" : "text-4xl font-bold text-gray-900"}>
                  Central Threat Intelligence Hub
                </h1>
                <p className={darkMode ? "text-gray-300 mt-2" : "text-gray-600 mt-2"}>
                  Fusion insights from CTIH, driven by all agents + community behavior.
                </p>
              </div>
              <Button onClick={fetchThreatIntel} variant="secondary" className="gap-2">
                <RefreshCcw className="w-4 h-4" />
                Refresh Intel
              </Button>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Badge variant="outline">Live</Badge>
              Updated by Pattern, Network, Behavior, and Biometric agents + CTIH feedback.
            </div>
          </motion.div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Trending Threat Receivers */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className={darkMode ? "text-2xl font-semibold text-white" : "text-2xl font-semibold text-gray-900"}>
                Trending Threat Receivers
              </h2>
              <p className="text-sm text-muted-foreground">Sorted by CTIH threat score</p>
            </div>
            <Separator />
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[...Array(4)].map((_, index) => (
                  <div key={index} className="h-40 rounded-xl bg-gradient-to-br from-gray-200/40 to-white animate-pulse dark:from-gray-700/30 dark:to-gray-800" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {trending.map((item, index) => (
                  <ThreatReceiverCard
                    key={item.receiver}
                    receiver={item.receiver}
                    score={item.threat_score ?? item.threatScore ?? 0}
                    patternFlags={item.pattern_flags ?? item.patternFlags ?? []}
                    cluster={receiverClusterMap[item.receiver]}
                    lastSeen={item.last_seen}
                    delay={index * 0.05}
                    onSelect={handleReceiverSelect}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Emerging Clusters */}
          {!loading && emergingClusters.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className={darkMode ? "text-2xl font-semibold text-white" : "text-2xl font-semibold text-gray-900"}>
                  Emerging Scam Clusters
                </h2>
                <p className="text-sm text-muted-foreground">New patterns detected in the last 7 days</p>
              </div>
              <Separator />
              {renderClusterGrid(emergingClusters, 'No emerging scam clusters this week.')}
            </div>
          )}

          {/* Scam Clusters */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className={darkMode ? "text-2xl font-semibold text-white" : "text-2xl font-semibold text-gray-900"}>
                Scam Clusters Overview
              </h2>
              <p className="text-sm text-muted-foreground">CTIH derived clusters</p>
            </div>
            <Separator />
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {[...Array(4)].map((_, index) => (
                  <div key={index} className="h-48 rounded-xl bg-gradient-to-br from-gray-200/40 to-white animate-pulse dark:from-gray-700/30 dark:to-gray-800" />
                ))}
              </div>
            ) : (
              renderClusterGrid(activeClusters, 'No active clusters yet.', 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6')
            )}
          </div>

          {/* Inactive clusters */}
          {!loading && inactiveClusters.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className={darkMode ? "text-2xl font-semibold text-white" : "text-2xl font-semibold text-gray-900"}>
                  Archived Clusters
                </h2>
                <p className="text-sm text-muted-foreground">Clusters that went quiet or below activity threshold</p>
              </div>
              <Separator />
              {renderClusterGrid(inactiveClusters, 'No archived clusters right now.', 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6')}
            </div>
          )}
        </div>
      </section>

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className="sm:max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Receiver Threat Timeline</SheetTitle>
            <SheetDescription>
              Investigate the historical context for <span className="font-semibold">{selectedReceiver}</span>
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6">
            <ThreatTimeline
              receiver={selectedReceiver}
              history={timelineState.history}
              loading={timelineState.loading}
              error={timelineState.error}
            />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};

export default ThreatIntelDashboard;

