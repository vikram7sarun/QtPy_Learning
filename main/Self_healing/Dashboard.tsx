// Dashboard.tsx
import { useWebSocket } from './hooks/useWebSocket';
import { useEffect, useState } from 'react';

const Dashboard = () => {
  const [healingData, setHealingData] = useState([]);
  const [selectorData, setSelectorData] = useState([]);

  const { data: wsData } = useWebSocket('ws://localhost:8000/ws');

  useEffect(() => {
    // Initial data load
    const fetchData = async () => {
      const [selectorsRes, reportsRes] = await Promise.all([
        fetch('/api/selectors'),
        fetch('/api/healing-reports')
      ]);

      const selectors = await selectorsRes.json();
      const reports = await reportsRes.json();

      setSelectorData(selectors);
      setHealingData(reports);
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (wsData) {
      // Update data based on WebSocket message
      if (wsData.type === 'healing_report') {
        setHealingData(prev => [wsData.data, ...prev]);
      } else if (wsData.type === 'selector_update') {
        setSelectorData(prev =>
          prev.map(selector =>
            selector.id === wsData.data.id ? wsData.data : selector
          )
        );
      }
    }
  }, [wsData]);

  // ... rest of the dashboard component
};