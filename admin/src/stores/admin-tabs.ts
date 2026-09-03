import { computed, ref } from "vue";
import { defineStore } from "pinia";

export type AdminTab = {
  key: string;
  path: string;
  title: string;
  closable: boolean;
};

const dashboardTab: AdminTab = {
  key: "/",
  path: "/",
  title: "控制台",
  closable: false,
};

export const useAdminTabsStore = defineStore("admin-tabs", () => {
  const tabs = ref<AdminTab[]>([{ ...dashboardTab }]);

  const tabKeys = computed(() => new Set(tabs.value.map((tab) => tab.key)));

  function ensureTab(tab: Omit<AdminTab, "closable"> & Partial<Pick<AdminTab, "closable">>) {
    if (tabKeys.value.has(tab.key)) {
      return;
    }
    tabs.value.push({ ...tab, closable: tab.closable ?? tab.key !== dashboardTab.key });
  }

  function removeTab(key: string) {
    if (key === dashboardTab.key) {
      return;
    }
    tabs.value = tabs.value.filter((tab) => tab.key !== key);
  }

  function removeOtherTabs(activeKey: string) {
    tabs.value = tabs.value.filter((tab) => !tab.closable || tab.key === activeKey);
  }

  function reset() {
    tabs.value = [{ ...dashboardTab }];
  }

  return { tabs, ensureTab, removeTab, removeOtherTabs, reset };
});
