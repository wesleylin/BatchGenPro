    def get_all_tasks(self, session_id):
        tasks = []
        try:
            keys = self.redis_client.keys(self._make_all_tasks_key(session_id))
            for key in keys:
                try:
                    task_data = self.redis_client.get(key)
                    if task_data:
                        tasks.append(json.loads(task_data))
                except (json.JSONDecodeError, Exception) as e:
                    # 如果某个任务数据损坏，跳过它
                    print(f"Error parsing task data for key {key}: {str(e)}")
                    continue
            return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
        except Exception as e:
            # Redis连接错误或其他错误
            print(f"Error getting tasks from Redis: {str(e)}")
            return []

